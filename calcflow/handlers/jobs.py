import os

from calcflow.core.job_submitter import submit_job, check_job_status, cancel_job
from calcflow.config.settings import get_config
from calcflow.handlers.common import pick_calc_dir
from calcflow.utils.prompts import ask, ask_int, ask_choice, ask_yes_no


def submit_job_handler(session):
    """401 - Submit a VASP job to SGE."""
    config = get_config()
    cluster = config.get("cluster", {})

    work_dir = pick_calc_dir(session)
    work_dir_name = os.path.basename(work_dir)

    name = ask("Job name",
               default=session.get("last_calc_name",
                                   os.environ.get("VASP_JOB_NAME", "calcflow_job")))

    vasp_cmd = ask_choice("VASP executable",
                          ["vasp_std", "vasp_gam", "vasp_neb"],
                          default=config.get("vasp", {}).get("default_executable", "vasp_std"))

    queue = ask("Queue", default=cluster.get("default_queue", "long"))
    nprocs = ask_int("Number of cores",
                     default=cluster.get("default_cores", 64), min_val=1)

    pe = cluster.get("parallel_env", "mpi-*")
    vasp_module = cluster.get("vasp_module", "vasp/6.4.0/")

    print("\n  Summary:")
    print(f"    Directory:    {work_dir_name}")
    print(f"    Job name:     {name}")
    print(f"    Executable:   {vasp_cmd}")
    print(f"    Queue:        {queue}")
    print(f"    Cores:        {nprocs}")
    print(f"    Parallel env: {pe}")
    print(f"    VASP module:  {vasp_module}")
    print()

    if not ask_yes_no("Submit this job?"):
        print("  Submission cancelled.")
        return

    job_id = submit_job(
        work_dir=work_dir,
        queue=queue,
        pe=pe,
        nprocs=nprocs,
        name=name,
        vasp_cmd=vasp_cmd,
        vasp_module=vasp_module,
    )

    session["last_job_id"] = job_id
    print(f"\n  Job submitted: {job_id}")


def check_status(session):  # pylint: disable=unused-argument
    """402 - Check job status."""
    output = check_job_status()
    print(f"\n{output}")


def cancel_job_handler(session):
    """403 - Cancel a job."""
    # Show current jobs first
    output = check_job_status()
    print(f"\n{output}")

    if not output.strip() or "no jobs" in output.lower():
        print("  No jobs to cancel.")
        return

    default_id = session.get("last_job_id", "")
    job_id = ask("Job ID to cancel", default=default_id if default_id else None)

    if not ask_yes_no(f"Cancel job {job_id}?"):
        print("  Cancellation aborted.")
        return

    result = cancel_job(job_id)
    print(f"\n  {result}")
