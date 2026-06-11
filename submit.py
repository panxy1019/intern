import time
from ray.job_submission import JobSubmissionClient

# 1. 连接到 Head 节点的 Dashboard 端口
client = JobSubmissionClient("http://10.42.0.23:8265")

print("🔄 正在打包并提交任务到 Ray 集群...")

# 2. 提交任务
#job_id = client.submit_job(
    # 集群执行的命令
 #   entrypoint="python test_vllm1.py",
    # runtime_env 的 working_dir 会把当前目录 (包括 test_npu.py) 打包传给集群
  #  runtime_env={
   #     "working_dir": "./"
    #}
#)

job_id = client.submit_job(
    entrypoint="python test_vll5.py",
    runtime_env={
        "working_dir": "./",
        },
)

print(f"✅ 任务已成功提交！")
print(f"🆔 Job ID: {job_id}")
print("-" * 50)
#print("📜 以下是集群实时传回的运行日志：\n")

# 3. 实时跟踪并打印集群的日志输出
#try:
#    for line in client.tail_job_logs(job_id):
#        print(line, end="")
#except KeyboardInterrupt:
#    print("\n\n⚠️ 你在本地按下了 Ctrl+C。")
#    print("ℹ️ 任务仍然在集群上继续运行。如果想停止它，请使用：")
#    print(f"    ray job stop {job_id} --address http://10.42.0.21:8265")

# 4. 获取最终状态
#status = client.get_job_status(job_id)
#print("\n" + "-" * 50)
#print(f"🏁 任务最终状态: {status}")