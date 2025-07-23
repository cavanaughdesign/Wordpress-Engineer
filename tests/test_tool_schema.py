import ast
import inspect
import os
import sys
from typing import Dict, Set, Any

# Ensure main.py can be imported
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

try:
    from main import tools as defined_tools_list, execute_tool
except ImportError as e:
    print(f"Error importing from main.py: {e}")
    print("Please ensure main.py is in the same directory as this script or in PYTHONPATH.")
    sys.exit(1)

class ExecuteToolVisitor(ast.NodeVisitor):
    """
    AST visitor to find tool handling blocks in execute_tool and parameters accessed from tool_input.
    """
    def __init__(self):
        self.handled_tools_info: Dict[str, Dict[str, Set[str]]] = {}
        self._current_tool_name_handling: str | None = None

    def visit_If(self, node: ast.If):
        original_tool_name_handling = self._current_tool_name_handling

        tool_name_in_condition = None
        if isinstance(node.test, ast.Compare) and \
           isinstance(node.test.left, ast.Name) and node.test.left.id == 'tool_name' and \
           isinstance(node.test.ops[0], ast.Eq):
            comparator = node.test.comparators[0]
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                tool_name_in_condition = comparator.value
            elif isinstance(comparator, ast.Str):  # Python < 3.8
                tool_name_in_condition = comparator.s
        
        if tool_name_in_condition:
            self._current_tool_name_handling = tool_name_in_condition
            if tool_name_in_condition not in self.handled_tools_info:
                self.handled_tools_info[tool_name_in_condition] = {"params_accessed": set()}
            
            for stmt_in_body in node.body:
                self.visit(stmt_in_body)
        else:
            # Not a tool_name check, or a more complex condition. Visit body under original context.
            for stmt_in_body in node.body:
                self.visit(stmt_in_body)

        # Process the 'orelse' part (elif or else)
        for orelse_stmt in node.orelse:
            self.visit(orelse_stmt)

        self._current_tool_name_handling = original_tool_name_handling

    def _extract_param_name_from_slice(self, sl_node: Any) -> str | None:
        param_name = None
        if isinstance(sl_node, ast.Constant) and isinstance(sl_node.value, str): # Py 3.9+ for direct constant slice
            param_name = sl_node.value
        elif isinstance(sl_node, ast.Index): # Common for Py < 3.9
            if isinstance(sl_node.value, ast.Constant) and isinstance(sl_node.value.value, str): # Py 3.8
                param_name = sl_node.value.value
            elif isinstance(sl_node.value, ast.Str): # Py < 3.8
                param_name = sl_node.value.s
        return param_name

    def visit_Subscript(self, node: ast.Subscript):
        if self._current_tool_name_handling and \
           isinstance(node.value, ast.Name) and node.value.id == 'tool_input':
            param_name = self._extract_param_name_from_slice(node.slice)
            if param_name and self._current_tool_name_handling in self.handled_tools_info: # Ensure key exists
                self.handled_tools_info[self._current_tool_name_handling]["params_accessed"].add(param_name)
        
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check for tool_input.get('param_name')
        if self._current_tool_name_handling and \
           isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and node.func.value.id == 'tool_input' and \
           node.func.attr == 'get' and len(node.args) >= 1:
            
            param_arg = node.args[0]
            param_name = None
            if isinstance(param_arg, ast.Constant) and isinstance(param_arg.value, str):
                param_name = param_arg.value
            elif isinstance(param_arg, ast.Str): # Python < 3.8
                param_name = param_arg.s
            
            if param_name and self._current_tool_name_handling in self.handled_tools_info: # Ensure key exists
                 self.handled_tools_info[self._current_tool_name_handling]["params_accessed"].add(param_name)
        
        self.generic_visit(node)

def get_handled_tools_info(func) -> Dict[str, Dict[str, Set[str]]]:
    source = inspect.getsource(func)
    tree = ast.parse(source)
    
    visitor = ExecuteToolVisitor()
    # The function itself is the first node in the parsed module's body
    if tree.body and isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        visitor.visit(tree.body[0]) 
    return visitor.handled_tools_info

def run_tests():
    print("Starting tool schema and execution analysis...\n")
    
    handled_tools_info = get_handled_tools_info(execute_tool)
    handled_tool_names_in_execute_tool = set(handled_tools_info.keys())
    
    defined_tool_schemas: Dict[str, Dict[str, Any]] = {}
    for tool_dict in defined_tools_list:
        if "name" in tool_dict and "input_schema" in tool_dict:
            defined_tool_schemas[tool_dict["name"]] = tool_dict["input_schema"]
        else:
            print(f"Warning: Tool definition missing 'name' or 'input_schema': {tool_dict.get('name', 'Unknown')}")

    defined_tool_names_from_list = set(defined_tool_schemas.keys())

    # --- Test Categories ---
    errors = []
    warnings = []
    success_count = 0

    # Test 1: Tools defined in list but not handled in execute_tool
    defined_but_not_handled = defined_tool_names_from_list - handled_tool_names_in_execute_tool
    for tool_name in defined_but_not_handled:
        errors.append(f"[ERROR] Tool '{tool_name}' is defined in tools list but NOT handled in execute_tool.")

    # Test 2: Tools handled in execute_tool but not defined in list
    handled_but_not_defined = handled_tool_names_in_execute_tool - defined_tool_names_from_list
    for tool_name in handled_but_not_defined:
        errors.append(f"[ERROR] Tool '{tool_name}' is handled in execute_tool but NOT defined in tools list.")

    # Test 3: Parameter consistency for tools that are both defined and handled
    for tool_name in defined_tool_names_from_list.intersection(handled_tool_names_in_execute_tool):
        schema = defined_tool_schemas[tool_name]
        schema_properties = schema.get("properties", {})
        schema_params = set(schema_properties.keys())
        required_schema_params = set(schema.get("required", []))
        
        accessed_params = handled_tools_info[tool_name]["params_accessed"]

        all_params_match = True

        # Accessed params not in schema
        for acc_param in accessed_params:
            if acc_param not in schema_params:
                errors.append(f"[ERROR] Tool '{tool_name}': Parameter '{acc_param}' accessed in execute_tool but NOT defined in its schema.")
                all_params_match = False
        
        # Required schema params not accessed
        for req_param in required_schema_params:
            if req_param not in accessed_params:
                # This could be a warning if tool_input is passed directly to a sub-handler
                warnings.append(f"[WARNING] Tool '{tool_name}': REQUIRED schema parameter '{req_param}' is NOT directly accessed from tool_input in execute_tool. (Verify handler if tool_input is passed directly).")
                all_params_match = False # Treat as potential issue

        # Optional schema params not accessed (less critical, could be informational)
        # for schema_param in schema_params - required_schema_params:
        #     if schema_param not in accessed_params:
        #         print(f"[INFO] Tool '{tool_name}': Optional schema parameter '{schema_param}' not directly accessed.")

        if all_params_match and not any(e.startswith(f"[ERROR] Tool '{tool_name}'") for e in errors):
             print(f"[SUCCESS] Tool '{tool_name}': Definition and handling appear consistent.")
             success_count +=1


    print("\n--- Test Summary ---")
    if not errors and not warnings:
        print("All tests passed! Tool definitions and execute_tool handling are consistent.")
    else:
        for e in errors:
            print(e)
        for w in warnings:
            print(w)
    
    print(f"\nTotal tools defined in list: {len(defined_tool_names_from_list)}")
    print(f"Total tools found handled in execute_tool: {len(handled_tool_names_in_execute_tool)}")
    print(f"Tools with consistent definition & handling: {success_count}")
    print(f"Errors found: {len(errors)}")
    print(f"Warnings found: {len(warnings)}")

if __name__ == "__main__":
    run_tests()