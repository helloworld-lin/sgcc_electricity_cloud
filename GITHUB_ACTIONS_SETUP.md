# GitHub Actions 云端部署教程

本教程将指导您如何使用GitHub Actions免费云服务自动获取国网电费数据，并在本地Home Assistant中读取这些数据。

## 部署架构

```
┌─────────────────────────┐
│   GitHub Actions        │
│   (云端定时运行)         │
│   - 每天自动登录国网     │
│   - 获取电费数据         │
│   - 保存为JSON文件       │
└────────┬────────────────┘
         │
         │ Git Push
         ▼
┌─────────────────────────┐
│   GitHub Repository     │
│   存储JSON数据文件       │
└────────┬────────────────┘
         │
         │ HTTPS读取
         ▼
┌─────────────────────────┐
│   本地Home Assistant    │
│   RESTful Sensor        │
│   读取并显示数据         │
└─────────────────────────┘
```

## 优势

✅ **完全免费** - GitHub Actions每月提供2000分钟免费额度，足够使用  
✅ **无需本地服务器** - 云端运行，不占用本地资源  
✅ **自动更新** - 每天定时自动获取数据  
✅ **数据安全** - 密码等敏感信息存储在GitHub Secrets中  

## 第一步：Fork本仓库到您的GitHub账号

1. 访问本项目的GitHub页面
2. 点击右上角的 "Fork" 按钮
3. 等待Fork完成

## 第二步：配置GitHub Secrets

在您Fork的仓库中配置敏感信息：

1. 进入您的仓库页面
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret` 添加以下密钥：

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `PHONE_NUMBER` | 国网登录手机号 | `13800138000` |
| `PASSWORD` | 国网登录密码 | `your_password` |
| `IGNORE_USER_ID` | 要忽略的用户ID（可选） | `xxxxx,xxxxx` 或留空 |

**添加步骤：**
- Name: 输入上表中的Secret名称（如 `PHONE_NUMBER`）
- Secret: 输入对应的值
- 点击 `Add secret`

## 第三步：启用GitHub Actions

1. 进入您的仓库页面
2. 点击顶部的 `Actions` 标签
3. 如果显示需要启用，点击 `I understand my workflows, go ahead and enable them`
4. 找到 `Fetch Electricity Data` workflow
5. 点击 `Enable workflow`

## 第四步：手动触发第一次运行（测试）

1. 在 `Actions` 页面，点击左侧的 `Fetch Electricity Data`
2. 点击右侧的 `Run workflow` 按钮
3. 点击绿色的 `Run workflow` 确认
4. 等待几分钟，查看运行结果

运行成功后，您会在仓库的 `data/electricity_data.json` 文件中看到获取的数据。

## 第五步：配置本地Home Assistant

### 5.1 安装RESTful集成（已内置，无需安装）

Home Assistant自带RESTful集成，直接配置即可。

### 5.2 编辑 configuration.yaml

在Home Assistant的配置文件中添加以下内容（替换 `YOUR_GITHUB_USERNAME` 为您的GitHub用户名，`YOUR_REPO_NAME` 为您Fork的仓库名）：

```yaml
# RESTful Sensor - 从GitHub获取国网电费数据
rest:
  - resource: "https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/master/data/electricity_data.json"
    scan_interval: 3600  # 每小时检查一次更新
    sensor:
      - name: "sgcc_data_status"
        value_template: "{{ value_json.status }}"
        json_attributes_path: "$"
        json_attributes:
          - timestamp
          - users

# Template Sensors - 解析数据并创建单独的传感器
template:
  - sensor:
      # 电费余额
      - name: "electricity_charge_balance"
        unique_id: electricity_charge_balance_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].balance | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "CNY"
        device_class: monetary
        state_class: total
        icon: mdi:cash
        attributes:
          user_id: >
            {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
            {% if users and users|length > 0 %}
              {{ users[0].user_id }}
            {% else %}
              unknown
            {% endif %}
          last_update: "{{ state_attr('sensor.sgcc_data_status', 'timestamp') }}"

      # 最近一天用电量
      - name: "last_electricity_usage"
        unique_id: last_electricity_usage_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].last_daily_usage | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: measurement
        icon: mdi:lightning-bolt
        attributes:
          date: >
            {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
            {% if users and users|length > 0 %}
              {{ users[0].last_daily_date }}
            {% else %}
              unknown
            {% endif %}

      # 今年总用电量
      - name: "yearly_electricity_usage"
        unique_id: yearly_electricity_usage_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].yearly_usage | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        icon: mdi:lightning-bolt

      # 今年总电费
      - name: "yearly_electricity_charge"
        unique_id: yearly_electricity_charge_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].yearly_charge | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "CNY"
        device_class: monetary
        state_class: total_increasing
        icon: mdi:cash

      # 上月用电量
      - name: "month_electricity_usage"
        unique_id: month_electricity_usage_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].month_usage | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: measurement
        icon: mdi:lightning-bolt

      # 上月电费
      - name: "month_electricity_charge"
        unique_id: month_electricity_charge_github
        state: >
          {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
          {% if users and users|length > 0 %}
            {{ users[0].month_charge | float(0) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "CNY"
        device_class: monetary
        state_class: measurement
        icon: mdi:cash
```

### 5.3 检查配置并重启

1. 在Home Assistant中，进入 `开发者工具` → `YAML`
2. 点击 `检查配置` 确保没有错误
3. 点击 `重新启动` 重启Home Assistant

## 第六步：查看传感器

重启后，您可以在Home Assistant中看到以下传感器：

- `sensor.electricity_charge_balance` - 电费余额
- `sensor.last_electricity_usage` - 最近一天用电量
- `sensor.yearly_electricity_usage` - 今年总用电量
- `sensor.yearly_electricity_charge` - 今年总电费
- `sensor.month_electricity_usage` - 上月用电量
- `sensor.month_electricity_charge` - 上月电费

## 自动运行时间

GitHub Actions会在以下时间自动运行：
- **每天早上7点**（北京时间）
- **每天晚上7点**（北京时间）

您也可以随时在GitHub Actions页面手动触发运行。

## 多用户支持

如果您的国网账号绑定了多个户号，JSON数据会包含所有户号的信息。您可以修改Home Assistant配置中的 `users[0]` 为 `users[1]`、`users[2]` 等来访问不同户号的数据。

示例（访问第二个户号）：
```yaml
state: >
  {% set users = state_attr('sensor.sgcc_data_status', 'users') %}
  {% if users and users|length > 1 %}
    {{ users[1].balance | float(0) }}
  {% else %}
    0
  {% endif %}
```

## 故障排查

### 1. GitHub Actions运行失败

- 检查Secrets是否正确配置
- 查看Actions运行日志，了解具体错误信息
- 确认国网账号密码是否正确
- 检查是否触发了国网的登录次数限制（每天有限次数）

### 2. Home Assistant没有数据

- 确认 `sensor.sgcc_data_status` 传感器是否存在
- 检查该传感器的属性中是否有 `users` 数据
- 确认GitHub仓库URL是否正确（注意替换用户名和仓库名）
- 尝试手动访问JSON文件URL，确认可以访问

### 3. 数据不更新

- 检查GitHub Actions是否正常运行
- 查看 `data/electricity_data.json` 文件的最后更新时间
- 确认Home Assistant的 `scan_interval` 设置（默认1小时检查一次）

## 安全建议

1. ✅ 使用GitHub Secrets存储敏感信息，不要直接写在代码中
2. ✅ Fork的仓库建议设为私有（Private Repository）
3. ✅ 定期更改国网账号密码
4. ✅ 如果不再使用，及时删除GitHub Secrets

## 高级配置

### 修改运行时间

编辑 `.github/workflows/fetch-electricity-data.yml` 文件中的 cron 表达式：

```yaml
schedule:
  - cron: '0 23 * * *'  # 早上7点北京时间（UTC时间-8小时）
  - cron: '0 11 * * *'  # 晚上7点北京时间
```

### 添加通知功能

您可以在获取数据后通过GitHub Actions发送通知到手机，具体可参考GitHub Actions的通知插件。

## 常见问题

**Q: GitHub Actions免费额度够用吗？**  
A: 完全够用。每次运行大约5-10分钟，每天2次，一个月最多使用600分钟，远低于2000分钟的免费额度。

**Q: 数据多久更新一次？**  
A: GitHub Actions每天运行2次（早晚各一次），Home Assistant每小时检查一次GitHub上的数据。

**Q: 可以同时使用Docker版本和GitHub Actions版本吗？**  
A: 可以，但建议只使用一种方式，避免频繁登录触发国网的安全限制。

**Q: 如何查看原始JSON数据？**  
A: 访问 `https://raw.githubusercontent.com/您的用户名/您的仓库名/master/data/electricity_data.json`

## 支持

如果您在使用过程中遇到问题，请在GitHub Issues中提问。

