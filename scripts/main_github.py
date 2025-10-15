import logging
import logging.config
import os
import sys
import json
from datetime import datetime
from const import *
from data_fetcher import DataFetcher
from error_watcher import ErrorWatcher

def main():
    global RETRY_TIMES_LIMIT
    
    # 读取环境变量
    try:
        PHONE_NUMBER = os.getenv("PHONE_NUMBER")
        PASSWORD = os.getenv("PASSWORD")
        JOB_START_TIME = os.getenv("JOB_START_TIME", "07:00")
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        VERSION = os.getenv("VERSION", "github-actions")
        RETRY_TIMES_LIMIT = int(os.getenv("RETRY_TIMES_LIMIT", 5))
        
        logger_init(LOG_LEVEL)
        logging.info(f"Running in GitHub Actions mode")
        logging.info(f"The current repository version is {VERSION}")
    except Exception as e:
        logging.error(f"Failed to read environment variables: {e}")
        sys.exit(1)
    
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"The current date is {current_datetime}.")
    
    # 初始化错误监控目录（与容器内逻辑一致，放到 /data/errors，Actions下用工作目录下的 data/errors）
    errors_root = os.path.abspath(os.path.join(os.getcwd(), "../data/errors"))
    os.makedirs(errors_root, exist_ok=True)
    ErrorWatcher.init(root_dir=errors_root)

    fetcher = DataFetcher(PHONE_NUMBER, PASSWORD)
    
    # 运行一次数据获取
    logging.info(f"Starting data fetch for user {PHONE_NUMBER}")
    run_task(fetcher)

def run_task(data_fetcher: DataFetcher):
    """运行数据获取任务并保存为JSON"""
    RETRY_TIMES_LIMIT = int(os.getenv("RETRY_TIMES_LIMIT", 5))
    
    for retry_times in range(1, RETRY_TIMES_LIMIT + 1):
        try:
            # 获取数据
            data = data_fetcher.fetch_for_github()
            
            if data:
                # 保存为JSON文件
                save_data_to_json(data)
                logging.info("Data successfully saved to JSON file")
            return
        except Exception as e:
            logging.error(f"State-refresh task failed, reason is [{e}], {RETRY_TIMES_LIMIT - retry_times} retry times left.")
            if retry_times == RETRY_TIMES_LIMIT:
                # 最后一次失败，也保存一个错误状态
                error_data = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "users": []
                }
                save_data_to_json(error_data)
            continue

def save_data_to_json(data):
    """将数据保存为JSON文件"""
    output_dir = "../data"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "electricity_data.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Data saved to {output_file}")

def logger_init(level: str):
    logger = logging.getLogger()
    logger.setLevel(level)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    format = logging.Formatter("%(asctime)s  [%(levelname)-8s] ---- %(message)s", "%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(format)
    logger.addHandler(sh)

if __name__ == "__main__":
    main()

