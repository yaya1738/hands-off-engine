"""
Job Application Agent Integration for Backend Loop
Add this to backend_loop.py
"""

def run_job_application_agent():
    """
    Run Job Application Agent - Autonomous job hunting.

    Sends applications, monitors responses, follows up.
    Part of the income generation pipeline.
    """
    try:
        from autonomous.job_application_agent import JobApplicationAgent

        agent = JobApplicationAgent()
        agent.run_cycle()

        return {
            "success": True,
            "applications_sent": agent.state["applications_sent"],
            "responses": agent.state["responses_received"],
            "interviews": agent.state["interviews_scheduled"],
            "last_send": agent.state["last_send"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add this to main loop (between module 12 and 13):
"""
        # 12.5 Job Application Agent - Autonomous income generation
        log("[12.5/26] Running Job Application Agent...")
        job_result = run_job_application_agent()
        state["job_agent"] = job_result
        if job_result.get("success"):
            log(f"  Applications sent: {job_result.get('applications_sent', 0)}")
            log(f"  Responses: {job_result.get('responses', 0)}")
            log(f"  Interviews: {job_result.get('interviews', 0)}")
            if job_result.get("last_send"):
                log(f"  Last send: {job_result['last_send']}")
        else:
            log(f"  Job Agent: {job_result.get('error', 'not configured')}")
"""
