import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  message,
  List,
  Tag,
  Space,
  Modal,
  Typography,
  Empty,
  Divider
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  SettingOutlined,
  BankOutlined,
  FileTextOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

interface JobConfig {
  id: string
  company: string
  position: string
  level?: string
  department?: string
  job_description?: string
  requirements?: string[]
  skills?: string[]
  is_default?: boolean
}

const JobPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobConfig[]>([])
  const [currentJob, setCurrentJob] = useState<JobConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingJob, setEditingJob] = useState<JobConfig | null>(null)
  const [form] = Form.useForm()

  // 获取岗位列表
  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/v1/jobs/list')
      if (response.ok) {
        const data = await response.json()
        setJobs(data)
      }
    } catch (error) {
      console.error('获取岗位列表失败:', error)
    }
  }

  // 获取当前岗位
  const fetchCurrentJob = async () => {
    try {
      const response = await fetch('/api/v1/jobs/current')
      if (response.ok) {
        const data = await response.json()
        setCurrentJob(data)
      }
    } catch (error) {
      console.error('获取当前岗位失败:', error)
    }
  }

  useEffect(() => {
    fetchJobs()
    fetchCurrentJob()
  }, [])

  // 打开创建/编辑弹窗
  const openModal = (job?: JobConfig) => {
    if (job) {
      setEditingJob(job)
      form.setFieldsValue({
        company: job.company,
        position: job.position,
        level: job.level,
        department: job.department,
        job_description: job.job_description,
        requirements: job.requirements?.join('\n') || '',
        skills: job.skills?.join('\n') || ''
      })
    } else {
      setEditingJob(null)
      form.resetFields()
    }
    setModalVisible(true)
  }

  // 关闭弹窗
  const closeModal = () => {
    setModalVisible(false)
    setEditingJob(null)
    form.resetFields()
  }

  // 保存岗位配置
  const handleSave = async (values: any) => {
    setLoading(true)
    try {
      const payload = {
        ...values,
        requirements: values.requirements?.split('\n').filter((r: string) => r.trim()) || [],
        skills: values.skills?.split('\n').filter((s: string) => s.trim()) || []
      }

      const url = editingJob
        ? `/api/v1/jobs/${editingJob.id}`
        : '/api/v1/jobs/create'
      
      const method = editingJob ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        message.success(editingJob ? '岗位配置更新成功' : '岗位配置创建成功')
        closeModal()
        fetchJobs()
        fetchCurrentJob()
      } else {
        const error = await response.json()
        message.error(error.detail || '保存失败')
      }
    } catch (error) {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  // 删除岗位配置
  const handleDelete = async (jobId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个岗位配置吗？',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/jobs/${jobId}`, {
            method: 'DELETE'
          })
          if (response.ok) {
            message.success('删除成功')
            fetchJobs()
            fetchCurrentJob()
          }
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  // 设置默认岗位
  const handleSetDefault = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/jobs/${jobId}/set-default`, {
        method: 'POST'
      })
      if (response.ok) {
        message.success('已设置为默认岗位')
        fetchJobs()
        fetchCurrentJob()
      }
    } catch (error) {
      message.error('设置失败')
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>
        <SettingOutlined /> 岗位设置
      </Title>
      <Text type="secondary">
        配置目标岗位信息，Agent将根据岗位要求调整面试策略
      </Text>

      <Divider />

      {/* 当前使用岗位 */}
      <Card
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            <span>当前使用岗位</span>
          </Space>
        }
        style={{ marginBottom: '24px' }}
      >
        {currentJob ? (
          <div>
            <Space size="large" style={{ marginBottom: '16px' }}>
              <Text strong style={{ fontSize: '18px' }}>
                <BankOutlined /> {currentJob.company}
              </Text>
              <Tag color="blue" style={{ fontSize: '14px', padding: '4px 12px' }}>
                {currentJob.position}
              </Tag>
              {currentJob.level && <Tag>{currentJob.level}</Tag>}
              {currentJob.department && <Tag>{currentJob.department}</Tag>}
            </Space>
            {currentJob.job_description && (
              <div style={{ marginTop: '16px' }}>
                <Text type="secondary">岗位描述：</Text>
                <div style={{ 
                  background: '#f5f5f5', 
                  padding: '12px', 
                  borderRadius: '4px',
                  marginTop: '8px',
                  whiteSpace: 'pre-wrap'
                }}>
                  {currentJob.job_description}
                </div>
              </div>
            )}
          </div>
        ) : (
          <Empty description="暂无岗位配置" />
        )}
      </Card>

      {/* 岗位列表 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>岗位配置列表</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal()}
          >
            新建岗位
          </Button>
        }
      >
        <List
          dataSource={jobs}
          renderItem={(job) => (
            <List.Item
              actions={[
                !job.is_default && (
                  <Button
                    key="default"
                    type="link"
                    onClick={() => handleSetDefault(job.id)}
                  >
                    设为默认
                  </Button>
                ),
                <Button
                  key="edit"
                  type="link"
                  icon={<EditOutlined />}
                  onClick={() => openModal(job)}
                >
                  编辑
                </Button>,
                <Button
                  key="delete"
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(job.id)}
                >
                  删除
                </Button>
              ].filter(Boolean)}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text strong>{job.company}</Text>
                    <Tag color="blue">{job.position}</Tag>
                    {job.is_default && (
                      <Tag color="success">当前使用</Tag>
                    )}
                  </Space>
                }
                description={
                  <Space>
                    {job.level && <span>职级：{job.level}</span>}
                    {job.department && <span>部门：{job.department}</span>}
                  </Space>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无岗位配置，请添加' }}
        />
      </Card>

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingJob ? '编辑岗位配置' : '新建岗位配置'}
        open={modalVisible}
        onCancel={closeModal}
        width={700}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{ is_default: false }}
        >
          <Form.Item
            name="company"
            label="公司名称"
            rules={[{ required: true, message: '请输入公司名称' }]}
          >
            <Input placeholder="例如：阿里巴巴" />
          </Form.Item>

          <Form.Item
            name="position"
            label="岗位名称"
            rules={[{ required: true, message: '请输入岗位名称' }]}
          >
            <Input placeholder="例如：产品经理" />
          </Form.Item>

          <Form.Item
            name="level"
            label="职级"
          >
            <Input placeholder="例如：P6、高级、资深（可选）" />
          </Form.Item>

          <Form.Item
            name="department"
            label="部门"
          >
            <Input placeholder="例如：用户增长部（可选）" />
          </Form.Item>

          <Form.Item
            name="job_description"
            label="岗位JD"
          >
            <TextArea
              rows={6}
              placeholder="请粘贴完整的岗位描述（JD），Agent会根据JD调整面试策略"
            />
          </Form.Item>

          <Form.Item
            name="requirements"
            label="岗位要求"
          >
            <TextArea
              rows={4}
              placeholder="每行一个要求，例如：&#10;3年以上产品经验&#10;熟悉电商行业&#10;具备良好的数据分析能力"
            />
          </Form.Item>

          <Form.Item
            name="skills"
            label="技能要求"
          >
            <TextArea
              rows={3}
              placeholder="每行一个技能，例如：&#10;Axure&#10;SQL&#10;数据分析"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={closeModal}>取消</Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                {editingJob ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default JobPage
