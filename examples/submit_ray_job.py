from ray.job_submission import JobSubmissionClient

RAY_DASHBOARD_URL = "http://10.42.0.23:8265"
ENTRYPOINT = "python examples/vllm_embedding_benchmark.py"
WORKING_DIR = "./"


def main() -> None:
    client = JobSubmissionClient(RAY_DASHBOARD_URL)

    print("正在打包并提交任务到 Ray 集群...")
    print(f"Dashboard: {RAY_DASHBOARD_URL}")
    print(f"Entrypoint: {ENTRYPOINT}")

    job_id = client.submit_job(
        entrypoint=ENTRYPOINT,
        runtime_env={"working_dir": WORKING_DIR},
    )

    print("任务已提交")
    print(f"Job ID: {job_id}")


if __name__ == "__main__":
    main()
