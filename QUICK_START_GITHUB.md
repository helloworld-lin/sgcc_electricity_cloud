# 🚀 GitHub Actions 部署快速指南

## 您需要做的事情（5分钟完成）

### 📋 准备工作
- 一个GitHub账号
- 国网账号和密码
- 本地运行的Home Assistant

---

## ✅ 步骤一：Fork本仓库

1. **访问本项目GitHub页面**
2. **点击右上角 "Fork" 按钮**
3. **等待Fork完成**（几秒钟）

---

## ✅ 步骤二：配置GitHub Secrets（重要！）

在您Fork的仓库中：

1. 点击 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下3个密钥：

| 名称 | 值 | 说明 |
|------|-----|------|
| `PHONE_NUMBER` | 您的手机号 | 国网登录账号 |
| `PASSWORD` | 您的密码 | 国网登录密码 |
| `IGNORE_USER_ID` | 留空或填写 | 要忽略的用户ID（可选） |

**每添加一个密钥：**
- Name: 输入表格中的名称
- Secret: 输入对应的值
- 点击 `Add secret`

---

## ✅ 步骤三：启用GitHub Actions

1. 进入您的仓库，点击顶部 `Actions` 标签
2. 点击 `I understand my workflows, go ahead and enable them`
3. 找到 `Fetch Electricity Data`，点击进入
4. 点击右侧 `Enable workflow`

---

## ✅ 步骤四：手动触发测试运行

1. 在 `Fetch Electricity Data` workflow页面
2. 点击 `Run workflow` → 确认 `Run workflow`
3. 等待3-5分钟，查看运行状态
4. ✅ 成功后，在仓库 `data/electricity_data.json` 可以看到数据

---

## ✅ 步骤五：配置本地Home Assistant

### 1. 获取您的JSON数据地址

格式：`https://raw.githubusercontent.com/您的GitHub用户名/sgcc_electricity_new-master/master/data/electricity_data.json`

**示例：**  
如果您的GitHub用户名是 `zhangsan`，那么地址是：  
`https://raw.githubusercontent.com/zhangsan/sgcc_electricity_new-master/master/data/electricity_data.json`

### 2. 编辑Home Assistant配置文件

打开 `configuration.yaml`，添加以下内容（**替换URL中的用户名**）：

```yaml
# RESTful Sensor - 从GitHub获取国网电费数据
rest:
  - resource: "https://raw.githubusercontent.com/您的GitHub用户名/sgcc_electricity_new-master/master/data/electricity_data.json"
    scan_interval: 3600
    sensor:
      - name: "sgcc_data_status"
        value_template: "{{ value_json.status }}"
        json_attributes_path: "$"
        json_attributes:
          - timestamp
          - users

# Template Sensors
template:
  - sensor:
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

### 3. 检查配置并重启

1. Home Assistant → `开发者工具` → `YAML` → `检查配置`
2. 确认无错误后，点击 `重新启动`

---

## 🎉 完成！

重启后，您将看到以下传感器：

- ⚡ `sensor.electricity_charge_balance` - 电费余额
- ⚡ `sensor.last_electricity_usage` - 最近一天用电量
- ⚡ `sensor.yearly_electricity_usage` - 今年总用电量
- ⚡ `sensor.yearly_electricity_charge` - 今年总电费
- ⚡ `sensor.month_electricity_usage` - 上月用电量
- ⚡ `sensor.month_electricity_charge` - 上月电费

---

## ⏰ 自动更新时间

GitHub Actions会自动运行：
- 每天早上 7:00（北京时间）
- 每天晚上 19:00（北京时间）

---

## 🔧 常见问题

**Q: GitHub Actions运行失败？**  
A: 检查Secrets配置是否正确，查看Actions日志了解错误详情

**Q: Home Assistant看不到数据？**  
A: 确认JSON URL是否正确，替换了您的GitHub用户名

**Q: 想修改运行时间？**  
A: 编辑 `.github/workflows/fetch-electricity-data.yml` 文件的cron表达式

**Q: 费用问题？**  
A: 完全免费！GitHub Actions提供每月2000分钟免费额度

---

## 📚 详细文档

查看完整教程：[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)

---

## ⚠️ 安全提示

1. ✅ 建议将Fork的仓库设为私有（Private）
2. ✅ 敏感信息必须存储在Secrets中，不要写在代码里
3. ✅ 定期更改国网密码

---

**祝您使用愉快！**

