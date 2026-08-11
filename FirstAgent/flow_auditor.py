import json
import sys
import os

class ContactFlowAuditor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.flow_data = self._load_flow()
        
    def _load_flow(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze(self):
        # Amazon Connect stores blocks in the 'Actions' array
        blocks = self.flow_data.get("Actions", [])
        
        total_blocks = len(blocks)
        total_edges = 0
        decision_branches = 0
        lambda_count = 0
        loop_risk_count = 0

        for block in blocks:
            block_type = block.get("Type", "")
            transitions = block.get("Transitions", {})
            
            # 1. Track risky external dependencies
            if "Lambda" in block_type or block_type == "InvokeLambdaFunction":
                lambda_count += 1
            
            # 2. Extract all outbound connections (Edges)
            outbound_paths = []
            
            # Standard sequential transition
            if transitions.get("NextAction"):
                outbound_paths.append(transitions["NextAction"])
                
            # Error branches
            for error_target in transitions.get("Errors", []):
                if error_target:
                    outbound_paths.append(error_target)
                    
            # Conditional branches (Check Attributes, Get Customer Input, etc.)
            for condition in transitions.get("Conditions", []):
                if isinstance(condition, dict) and condition.get("NextAction"):
                    outbound_paths.append(condition["NextAction"])
                elif isinstance(condition, str):
                    outbound_paths.append(condition)

            edge_count = len(outbound_paths)
            total_edges += edge_count
            
            # 3. Calculate branching points for D + 1 Complexity
            if edge_count > 1:
                decision_branches += (edge_count - 1)
                
            # Check for generic error looping risk (missing explicit error branches)
            if "Errors" in transitions and len(transitions.get("Errors", [])) == 0:
                if block_type in ["InvokeLambdaFunction", "Transfer", "GetCustomerInput"]:
                    loop_risk_count += 1

        # Complexity Calculations
        # McCabe Formula: M = E - N + 2P (Assuming P=1 for single contact flow)
        mccabe_score = total_edges - total_blocks + 2 if total_blocks > 0 else 1
        # Alternative Decision Formula: CC = D + 1
        decision_score = decision_branches + 1

        return {
            "flow_name": self.flow_data.get("Name", os.path.basename(self.file_path)),
            "total_blocks": total_blocks,
            "total_edges": total_edges,
            "cyclomatic_complexity_mccabe": mccabe_score,
            "cyclomatic_complexity_decision": decision_score,
            "lambda_integrations": lambda_count,
            "unhandled_error_blocks": loop_risk_count
        }

    def generate_report(self):
        metrics = self.analyze()
        cc = metrics["cyclomatic_complexity_mccabe"]
        blocks = metrics["total_blocks"]
        
        # Determine status thresholds
        cc_status = "🟢 PASS (Low Risk)" if cc <= 10 else "🟡 WARN (Moderate Risk)" if cc <= 20 else "🔴 FAIL (Refactor Immediately)"
        block_status = "🟢 PASS" if blocks <= 50 else "🔴 WARN (Bloated UI Graph)"

        print("=" * 50)
        print(f"AMAZON CONNECT FLOW AUDIT REPORT: {metrics['flow_name']}")
        print("=" * 50)
        print(f"Total Logic Blocks (N):       {blocks} [{block_status}]")
        print(f"Total Structural Edges (E):   {metrics['total_edges']}")
        print(f"McCabe Complexity Score (M): {cc} [{cc_status}]")
        print(f"Decision Point Score (D+1):   {metrics['cyclomatic_complexity_decision']}")
        print("-" * 50)
        print(f"AWS Lambda Dependencies:      {metrics['lambda_integrations']}")
        print(f"Missing Error Handlers:       {metrics['unhandled_error_blocks']}")
        print("=" * 50)
        
        # Set exit code 1 if metrics fail threshold (Ideal for CI/CD pipelines)
        if cc > 20 or blocks > 60:
            sys.exit(1)
        sys.exit(0)

if __name__ == "__main__":
    # To use: python flow_auditor.py my_contact_flow.json
    if len(sys.argv) < 2:
        print("Error: Please provide the path to your Amazon Connect Flow JSON file.")
        print("Usage: python flow_auditor.py <path_to_json>")
        sys.exit(1)
        
    auditor = ContactFlowAuditor(sys.argv[1])
    auditor.generate_report()
