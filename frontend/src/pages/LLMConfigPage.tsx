import React, { useState, useEffect } from 'react'
import { Card, Button, Table, Modal, Form, Input, Space, Tag, message, Popconfirm, Select, Tooltip } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, SettingOutlined, InfoCircleOutlined } from '@ant-design/icons'

const { Option } = Select

interface LLMConfig {
  id: string
  name: string
  model: string
  base_url: string
  api_key: string
  is_default: boolean
  is_active: boolean
}

interface PresetModel {
  [key: string]: string
}

const LLMConfigPage: React.FC = () => {
  const [configs, setConfigs] = useState<LLMConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null)
  const [presetModels, setPresetModels] = useState<PresetModel>({})
  const [form] = Form.useForm()
  const [testLoading, setTestLoading] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [modelInfo, setModelInfo] = useState<any>(null)

  // 获取配置列表
  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/llm-configs/list')
      if (!response.ok) {
        throw new Error('获取配置失败')
      }
      const data = await response.json()
      setConfigs(data.configs || [])
    } catch (error) {
      console.error('获取配置失败:', error)
      message.error('获取配置列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取预设模型列表
  const fetchPresetModels = async () => {
    try {
      const response = await fetch('/api/v1/llm-configs/preset-models')
      if (response.ok) {
        const data = await response.json()
        setPresetModels(data.models || {})
      }
    } catch (error) {
      console.error('获取预设模型失败:', error)
    }
  }

  useEffect(() => {
    fetchConfigs()
    fetchPresetModels()
  }, [])

  // 打开新增/编辑模态框
  const handleOpenModal = (config?: LLMConfig) => {
    if (config) {
      setEditingConfig(config)
      setSelectedModel(config.model)
      form.setFieldsValue({
        name: config.name,
        model: config.model,
        base_url: config.base_url,
        api_key: '' // 不显示真实 API key
      })
    } else {
      setEditingConfig(null)
      setSelectedModel('')
      form.resetFields()
      form.setFieldsValue({
        base_url: 'https://api.moonshot.cn/v1',
        model: 'kimi-k2.5'
      })
    }
    setModalVisible(true)
  }

  // 处理模型选择变化
  const handleModelChange = (value: string) => {
    setSelectedModel(value)
    
    // 根据模型自动设置推荐的 Base URL
    const modelLower = value.toLowerCase()
    let recommendedUrl = ''
    
    if (modelLower.includes('kimi') || modelLower.includes('moonshot')) {
      recommendedUrl = 'https://api.moonshot.cn/v1'
    } else if (modelLower.includes('gpt') || modelLower.includes('openai')) {
      recommendedUrl = 'https://api.openai.com/v1'
    } else if (modelLower.includes('claude')) {
      recommendedUrl = 'https://api.anthropic.com'
    } else if (modelLower.includes('deepseek')) {
      recommendedUrl = 'https://api.deepseek.com/v1'
    } else if (modelLower.includes('gemini')) {
      recommendedUrl = 'https://generativelanguage.googleapis.com/v1beta'
    }
    
    if (recommendedUrl && !editingConfig) {
      form.setFieldsValue({ base_url: recommendedUrl })
    }
  }

  // 保存配置
  const handleSave = async (values: any) => {
    try {
      const url = editingConfig 
        ? `/api/v1/llm-configs/${editingConfig.id}`
        : '/api/v1/llm-configs/create'
      
      const method = editingConfig ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      })

      if (!response.ok) {
        throw new Error('保存失败')
      }

      const result = await response.json()
      
      message.success(
        <span>
          {editingConfig ? '配置更新成功' : '配置创建成功'}
          <br />
          <small>模型: {result.model}, Temperature: {result.temperature}</small>
        </span>
      )
      setModalVisible(false)
      fetchConfigs()
    } catch (error) {
      console.error('保存配置失败:', error)
      message.error('保存配置失败')
    }
  }

  // 删除配置
  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/llm-configs/${id}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      message.success('配置删除成功')
      fetchConfigs()
    } catch (error) {
      console.error('删除配置失败:', error)
      message.error('删除配置失败')
    }
  }

  // 测试配置
  const handleTest = async (config: LLMConfig) => {
    setTestLoading(config.id)
    try {
      const response = await fetch(`/api/v1/llm-configs/${config.id}/test`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('测试失败')
      }

      const data = await response.json()
      if (data.success) {
        message.success(`测试成功！延迟: ${data.latency_ms}ms, 模型: ${data.model}`)
      } else {
        message.error(`测试失败: ${data.message}`)
      }
    } catch (error) {
      console.error('测试配置失败:', error)
      message.error('测试配置失败')
    } finally {
      setTestLoading(null)
    }
  }

  // 设置默认配置
  const handleSetDefault = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/llm-configs/${id}/set-default`, {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('设置失败')
      }

      message.success('默认配置设置成功')
      fetchConfigs()
    } catch (error) {
      console.error('设置默认配置失败:', error)
      message.error('设置默认配置失败')
    }
  }

  const columns = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: LLMConfig) => (
        <Space>
          {text}
          {record.is_default && <Tag color="blue">默认</Tag>}
          {!record.is_active && <Tag color="red">已禁用</Tag>}
        </Space>
      )
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      render: (text: string) => (
        <Tag color="green">{text}</Tag>
      )
    },
    {
      title: 'Base URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      render: (text: string) => (
        <span>{text ? `${text.substring(0, 8)}****` : '未设置'}</span>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: LLMConfig) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<CheckCircleOutlined />}
            loading={testLoading === record.id}
            onClick={() => handleTest(record)}
          >
            测试
          </Button>
          {!record.is_default && (
            <Button
              size="small"
              onClick={() => handleSetDefault(record.id)}
            >
              设为默认
            </Button>
          )}
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          />
          <Popconfirm
            title="确定要删除这个配置吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <SettingOutlined />
            <span>LLM 配置管理</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增配置
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑配置' : '新增配置'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            name="name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="例如：Kimi Moonshot" />
          </Form.Item>

          <Form.Item
            name="model"
            label={
              <Space>
                模型
                <Tooltip title="选择模型后，Temperature、Max Tokens 等参数会自动匹配">
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Tooltip>
              </Space>
            }
            rules={[{ required: true, message: '请选择或输入模型' }]}
          >
            <Select
              placeholder="选择或输入模型名称"
              showSearch
              allowClear
              onChange={handleModelChange}
              dropdownRender={(menu) => (
                <>
                  {menu}
                  <div style={{ padding: '8px 12px', borderTop: '1px solid #e8e8e8', marginTop: 4 }}>
                    <small style={{ color: '#999' }}>支持自定义输入模型名称</small>
                  </div>
                </>
              )}
            >
              {Object.entries(presetModels).map(([key, description]) => (
                <Option key={key} value={key}>
                  <Space direction="vertical" size={0} style={{ display: 'flex' }}>
                    <span style={{ fontWeight: 'bold' }}>{key}</span>
                    <span style={{ fontSize: 12, color: '#999' }}>{description}</span>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="base_url"
            label="Base URL"
            rules={[{ required: true, message: '请输入 Base URL' }]}
          >
            <Input placeholder="https://api.moonshot.cn/v1" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: !editingConfig, message: '请输入 API Key' }]}
          >
            <Input.Password 
              placeholder={editingConfig ? '留空表示不修改' : 'sk-...'}
            />
          </Form.Item>

          {selectedModel && (
            <div style={{ 
              background: '#f6ffed', 
              border: '1px solid #b7eb8f', 
              borderRadius: 4, 
              padding: 12,
              marginTop: 16
            }}>
              <div style={{ fontWeight: 'bold', color: '#52c41a', marginBottom: 8 }}>
                自动匹配参数
              </div>
              <div style={{ fontSize: 13, color: '#666' }}>
                <div>• Temperature、Max Tokens 等参数会根据所选模型自动设置</div>
                <div>• 无需手动配置，避免参数不兼容问题</div>
                <div>• 如需使用其他模型参数，请直接选择对应的模型</div>
              </div>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default LLMConfigPage
