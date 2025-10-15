# Render 部署指南（实验性）

## ⚠️ 重要提示

**成功率约30%** - Render使用云端IP，可能被国网网站拦截，导致和GitHub Actions一样的 `.user` 元素找不到问题。

**如果失败，建议改用：**
- 本地Docker部署（100%成功）
- 国内云服务器（成功率较高）

---

## 📋 部署步骤

### 1. 注册Render账号

访问 https://render.com 注册（可用GitHub账号登录，无需信用卡）

### 2. 连接GitHub仓库

1. 登录Render Dashboard
2. 点击 "New" → "Web Service"
3. 选择 "Connect a repository"
4. 连接您的GitHub账号
5. 选择 `sgcc_electricity_cloud` 仓库

### 3. 配置服务

Render会自动检测到 `render.yaml` 配置文件：

- **Name**: sgcc-electricity
- **Environment**: Docker
- **Plan**: Free

### 4. 设置环境变量

在 "Environment" 标签页添加：

| 变量名 | 值 |
|--------|-----|
| `PHONE_NUMBER` | 您的国网手机号 |
| `PASSWORD` | 您的国网密码 |

### 5. 部署

点击 "Create Web Service" 开始部署

---

## 🧪 测试

部署完成后，访问以下端点测试：

- **健康检查**: `https://your-service.onrender.com/health`
  - 返回 `OK` 表示服务正常

- **触发数据获取**: `https://your-service.onrender.com/trigger`
  - 手动触发一次数据获取

- **查看数据**: `https://your-service.onrender.com/data`
  - 返回JSON格式的电费数据

---

## 📅 定时任务

### 免费方案（使用外部定时器）

使用 https://cron-job.org （免费）：

1. 注册cron-job.org账号
2. 创建新任务
3. URL: `https://your-service.onrender.com/trigger`
4. 时间表: `0 7,19 * * *` （每天7点和19点）
5. 保存

### 付费方案（Render Cron Jobs）

升级到付费计划（$7/月），可使用内置Cron Jobs

---

## 🏠 配置Home Assistant

使用您的Render服务地址：

```yaml
rest:
  - resource: "https://your-service.onrender.com/data"
    scan_interval: 3600
    sensor:
      - name: "sgcc_data_status"
        value_template: "{{ value_json.status }}"
        json_attributes_path: "$"
        json_attributes:
          - timestamp
          - users

template:
  - sensor:
      - name: "electricity_charge_balance"
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].balance | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "CNY"
        device_class: monetary
        # ... 其他传感器配置类似
```

---

## 🐛 常见问题

**Q: 部署后访问 /trigger 没反应？**  
A: 查看Render日志，很可能遇到 `.user` 元素找不到（云端IP被拦截）

**Q: 服务休眠了？**  
A: 免费版15分钟无请求会休眠，下次访问会唤醒（需要等待）

**Q: 内存不足？**  
A: 免费版512MB可能不够，考虑升级或本地部署

---

## 💡 如果Render失败

**强烈建议改用本地部署：**

```bash
cd sgcc_electricity_new-master
docker-compose up -d
```

本地部署使用家庭IP，100%成功，且可直接推送到Home Assistant。

