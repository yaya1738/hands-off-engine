from datetime import datetime, timezone


class FactoryConsolidationAuthority:

    def evaluate(self, consolidation_report):

        decisions = consolidation_report.get(
            "decisions",
            {}
        )

        plan = {
            "preserve": [],
            "review": [],
            "merge_candidates": [],
            "retire_candidates": [],
        }

        for name, item in decisions.items():

            decision = item.get(
                "decision"
            )

            if decision == "preserve":
                plan["preserve"].append(name)

            elif decision == "review_owner":
                plan["review"].append(name)

            elif decision == "merge_candidate":
                plan["merge_candidates"].append(name)

            elif decision == "retire_candidate":
                plan["retire_candidates"].append(name)


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_consolidation_authority",

            "plan":
                plan,

            "status":
                "decision_plan_created"
        }
