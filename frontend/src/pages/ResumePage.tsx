import React, { useState, useEffect } from 'react'
import { Card, Upload, Button, List, Tag, message, Typography, Space, Modal, Row, Col } from 'antd'
import { UploadOutlined, FileTextOutlined, DeleteOutlined, CheckCircleOutlined, EyeOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import ResumeVisualization from '../components/ResumeVisualization'

const { Title, Text } = Typography

interface Resume {
  id: string
  file_name: string
  is_active: boolean
  created_at: string
  parsed_data: {
    name: string
    phone?: string
    email?: string
    location?: string
    gender?: string
    age?: number
    summary?: string
    education: Array<{
      school: string
      major: string
      degree: string
    }>
    experience: Array<{
      company: string
      position: string
    }>
    projects?: Array<{
      name: string
      description?: string
      role?: string
    }>
  }
}

const ResumePage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [loading, setLoading] = useState(false)
  const [currentResume, setCurrentResume] = useState<Resume | null>(null)

  // 获取简历列表
  const fetchResumes = async () => {
    try {
      const response = await fetch('/api/v1/resumes/list')
      if (response.ok) {
        const data = await response.json()
        setResumes(data)
        // 找到当前激活的简历
        const active = data.find((r: Resume) => r.is_active)
        setCurrentResume(active || null)
      }
    } catch (error) {
      console.error('获取简历列表失败:', error)
    }
  }

  useEffect(() => {
    fetchResumes()
  }, [])

  // 上传简历
  const handleUpload = async (file: UploadFile) => {
    setLoading(true)
    const formData = new FormData()
    formData.append('file', file as any)

    try {
      const response = await fetch('/api/v1/resumes/upload', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        message.success('简历上传成功')
        fetchResumes()
      } else {
        const error = await response.json()
        message.error(error.detail || '上传失败')
      }
    } catch (error) {
      message.error('上传失败')
    } finally {
      setLoading(false)
    }
    return false // 阻止默认上传行为
  }

  // 激活简历
  const handleActivate = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/resumes/${id}/activate`, {
        method: 'POST'
      })
      if (response.ok) {
        message.success('简历已激活')
        fetchResumes()
      }
    } catch (error) {
      message.error('激活失败')
    }
  }

  // 删除简历
  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这份简历吗？',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/resumes/${id}`, {
            method: 'DELETE'
          })
          if (response.ok) {
            message.success('简历已删除')
            fetchResumes()
          }
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>简历管理</Title>
      <Text type="secondary">上传简历后，Agent将以该简历身份回答面试问题</Text>

      <Card style={{ marginTop: '24px', marginBottom: '24px' }}>
        <Upload
          beforeUpload={handleUpload}
          accept=".docx"
          showUploadList={false}
        >
          <Button
            type="primary"
            icon={<UploadOutlined />}
            loading={loading}
            size="large"
          >
            上传简历 (.docx)
          </Button>
        </Upload>
        <Text type="secondary" style={{ marginLeft: '16px' }}>
          支持 Word 格式 (.docx)，最大 10MB
        </Text>
      </Card>

      {currentResume && (
        <Card
          title="当前使用的简历"
          style={{ marginBottom: '24px', borderColor: '#52c41a' }}
          headStyle={{ background: '#f6ffed', borderBottom: '1px solid #b7eb8f' }}
        >
          <Row gutter={24}>
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <FileTextOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                  <Text strong>{currentResume.file_name}</Text>
                  <Tag color="success">当前使用</Tag>
                </Space>
                
                {/* 用户信息 */}
                <div>
                  <Text type="secondary" strong>用户信息: </Text>
                  <Space wrap>
                    <Text>姓名: {currentResume.parsed_data?.name || '未解析'}</Text>
                    {currentResume.parsed_data?.gender && <Tag>{currentResume.parsed_data.gender}</Tag>}
                    {currentResume.parsed_data?.age && <Tag>{currentResume.parsed_data.age}岁</Tag>}
                    {currentResume.parsed_data?.phone && <Tag icon={<span>📱</span>}>{currentResume.parsed_data.phone}</Tag>}
                    {currentResume.parsed_data?.email && <Tag icon={<span>📧</span>}>{currentResume.parsed_data.email}</Tag>}
                    {currentResume.parsed_data?.location && <Tag icon={<span>📍</span>}>{currentResume.parsed_data.location}</Tag>}
                  </Space>
                </div>
                
                {/* 教育背景 */}
                <div>
                  <Text type="secondary" strong>教育背景: </Text>
                  {currentResume.parsed_data?.education?.map((edu, index) => (
                    <Tag key={index}>{edu.school} · {edu.major}</Tag>
                  ))}
                </div>
                
                {/* 工作经历 */}
                <div>
                  <Text type="secondary" strong>工作经历: </Text>
                  {currentResume.parsed_data?.experience?.map((exp, index) => (
                    <Tag key={index}>{exp.company} · {exp.position}</Tag>
                  ))}
                </div>
                
                {/* 项目经历 */}
                {currentResume.parsed_data?.projects && currentResume.parsed_data.projects.length > 0 && (
                  <div>
                    <Text type="secondary" strong>项目经历: </Text>
                    {currentResume.parsed_data.projects.map((proj, index) => (
                      <Tag key={index} color="purple">{proj.name} {proj.role && `· ${proj.role}`}</Tag>
                    ))}
                  </div>
                )}
              </Space>
            </Col>
            <Col span={16}>
              {currentResume.parsed_data && (
                <ResumeVisualization data={currentResume.parsed_data} />
              )}
            </Col>
          </Row>
        </Card>
      )}

      <Card title="简历列表">
        <List
          dataSource={resumes}
          renderItem={(resume) => (
            <List.Item
              actions={[
                !resume.is_active && (
                  <Button
                    type="link"
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleActivate(resume.id)}
                  >
                    激活
                  </Button>
                ),
                <Button
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(resume.id)}
                >
                  删除
                </Button>
              ].filter(Boolean)}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: '32px', color: '#1890ff' }} />}
                title={
                  <Space>
                    <Text strong>{resume.file_name}</Text>
                    {resume.is_active && <Tag color="success">当前使用</Tag>}
                  </Space>
                }
                description={
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">
                      姓名: {resume.parsed_data?.name || '未解析'}
                    </Text>
                    <Text type="secondary">
                      上传时间: {new Date(resume.created_at).toLocaleString()}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  )
}

export default ResumePage
