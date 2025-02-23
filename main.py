import os
import dashscope
import subprocess


def get_today_commits():
    cmd = 'git log --since="0:00" --until="23:59" --pretty=format:"%s"'
#    cmd = 'git -v'
    result = subprocess.check_output(cmd, shell=True)
    return result.decode('utf-8').split('\n')


def main():
    commits = get_today_commits()
    print(commits)
    messages = [
        {'role': 'user', 'content': '你是谁？'},

    ]
    response = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key='sk-6c7638170cb84af48685a33370a5e8d9',
        model="qwen-plus",
        # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=messages,
        result_format='message'
    )
    print(response)

if __name__ == "__main__":
    main()