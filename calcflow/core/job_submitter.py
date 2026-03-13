import os
import subprocess
import logging

from jinja2 import Environment, PackageLoader

from calcflow import JobSubmissionError

_jinja_env = Environment(loader=PackageLoader("calcflow", "data/templates"))


def render_submission_script(vasp_cmd, vasp_module, work_dir):
    """Render the SGE submission script from template."""
    template = _jinja_env.get_template("sge.sh.j2")
    return template.render(
        vasp_cmd=vasp_cmd,
        vasp_module=vasp_module,
        work_dir=work_dir,
    )


def create_submission_script(work_dir, vasp_cmd="vasp_std", vasp_module="vasp/6.4.0/"):
    """Write the qscript file to the working directory."""
    script_content = render_submission_script(vasp_cmd, vasp_module, work_dir)
    script_path = os.path.join(work_dir, "qscript")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    logging.info("Submission script written to %s", script_path)
    return script_path


def submit_job(work_dir, queue="long", pe="mpi-*", nprocs=64, name="calcflow_job",
               vasp_cmd="vasp_std", vasp_module="vasp/6.4.0/"):
    """
    Create submission script and submit to SGE.

    Returns the job ID string on success.
    """
    create_submission_script(work_dir, vasp_cmd, vasp_module)

    cmd = [
        "qsub", "-o", work_dir, "-j", "y",
        "-N", name, "-q", queue,
        "-pe", pe, str(nprocs),
        os.path.join(work_dir, "qscript"),
    ]

    logging.info("Submitting: %s", ' '.join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        job_id = result.stdout.strip()
        logging.info("Job submitted successfully. ID: %s", job_id)
        return job_id
    except subprocess.CalledProcessError as e:
        raise JobSubmissionError(f"Job submission failed: {e.stderr}") from e


def check_job_status():
    """Run qstat to check current user's jobs."""
    try:
        result = subprocess.run(
            ["qstat", "-u", os.environ.get("USER", "")],
            capture_output=True, text=True, check=False,
        )
        return result.stdout if result.stdout.strip() else "No jobs currently running."
    except FileNotFoundError:
        return "qstat not found. Are you on a cluster with SGE?"


def cancel_job(job_id):
    """Cancel an SGE job by ID."""
    try:
        result = subprocess.run(
            ["qdel", str(job_id)],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() or f"Job {job_id} cancelled."
    except subprocess.CalledProcessError as e:
        raise JobSubmissionError(f"Failed to cancel job {job_id}: {e.stderr}") from e
