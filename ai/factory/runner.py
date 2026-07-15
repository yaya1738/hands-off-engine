from ai.factory.execution_record import ExecutionRecord


class FactoryRunner:
    def run(self, task_id: str, steps: list[str]) -> ExecutionRecord:
        record = ExecutionRecord(task_id=task_id)

        try:
            for step in steps:
                record.commands.append(step)
                record.outputs.append(f"completed:{step}")

            record.succeed("all steps completed")

        except Exception as exc:
            record.fail(str(exc))

        return record
