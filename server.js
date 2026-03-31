#!/usr/bin/env node
/**
 * 需求管理系统 - Node.js 版本
 * 支持多人协作、数据持久化
 */

const express = require('express');
const cors = require('cors');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static('requirement_app'));

// 初始化 Supabase 客户端
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.warn('⚠️  警告：未配置 Supabase 环境变量，将使用内存存储（重启后数据丢失）');
    console.warn('请在 Vercel 控制台设置 SUPABASE_URL 和 SUPABASE_ANON_KEY');
}

const supabase = supabaseUrl && supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

// 内存存储（备用方案）
let inMemoryProjects = [];
let inMemoryRequirements = [];

// API 路由

// 获取所有项目
app.get('/api/get_projects', async (req, res) => {
    try {
        if (supabase) {
            const { data, error } = await supabase
                .from('projects')
                .select('*')
                .order('created_date', { ascending: false });
            
            if (error) throw error;
            
            res.json({
                success: true,
                projects: data || []
            });
        } else {
            res.json({
                success: true,
                projects: inMemoryProjects
            });
        }
    } catch (error) {
        console.error('Error fetching projects:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 添加项目
app.post('/api/add_project', async (req, res) => {
    try {
        const { name, owner, description } = req.body;
        
        if (!name) {
            return res.status(400).json({
                success: false,
                error: '缺少项目名称'
            });
        }
        
        const project = {
            name: name.trim(),
            owner: (owner || '').trim(),
            description: (description || '').trim(),
            created_date: new Date().toISOString()
        };
        
        if (supabase) {
            const { data, error } = await supabase
                .from('projects')
                .insert([project])
                .select();
            
            if (error) throw error;
            
            res.json({
                success: true,
                id: data[0].id,
                message: `项目 "${name}" 添加成功`
            });
        } else {
            project.id = inMemoryProjects.length + 1;
            inMemoryProjects.push(project);
            
            res.json({
                success: true,
                id: project.id,
                message: `项目 "${name}" 添加成功`
            });
        }
    } catch (error) {
        console.error('Error adding project:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 更新项目
app.put('/api/update_project/:id', async (req, res) => {
    try {
        const projectId = parseInt(req.params.id);
        const { name, owner, description } = req.body;
        
        if (!name) {
            return res.status(400).json({
                success: false,
                error: '缺少项目名称'
            });
        }
        
        if (supabase) {
            const { data, error } = await supabase
                .from('projects')
                .update({
                    name: name.trim(),
                    owner: (owner || '').trim(),
                    description: (description || '').trim()
                })
                .eq('id', projectId)
                .select();
            
            if (error) throw error;
            
            if (data.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: '项目不存在'
                });
            }
            
            res.json({
                success: true,
                message: '项目已更新'
            });
        } else {
            const index = inMemoryProjects.findIndex(p => p.id === projectId);
            if (index === -1) {
                return res.status(404).json({
                    success: false,
                    error: '项目不存在'
                });
            }
            
            inMemoryProjects[index] = {
                ...inMemoryProjects[index],
                name: name.trim(),
                owner: (owner || '').trim(),
                description: (description || '').trim()
            };
            
            res.json({
                success: true,
                message: '项目已更新'
            });
        }
    } catch (error) {
        console.error('Error updating project:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 删除项目
app.delete('/api/delete_project/:id', async (req, res) => {
    try {
        const projectId = parseInt(req.params.id);
        
        if (supabase) {
            const { error } = await supabase
                .from('projects')
                .delete()
                .eq('id', projectId);
            
            if (error) throw error;
            
            res.json({
                success: true,
                message: '项目已删除'
            });
        } else {
            const index = inMemoryProjects.findIndex(p => p.id === projectId);
            if (index === -1) {
                return res.status(404).json({
                    success: false,
                    error: '项目不存在'
                });
            }
            
            inMemoryProjects.splice(index, 1);
            
            res.json({
                success: true,
                message: '项目已删除'
            });
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 获取所有需求
app.get('/api/get_requirements', async (req, res) => {
    try {
        if (supabase) {
            const { data, error } = await supabase
                .from('requirements')
                .select('*')
                .order('created_date', { ascending: false });
            
            if (error) throw error;
            
            res.json({
                success: true,
                requirements: data || [],
                stats: getStatistics(data || [])
            });
        } else {
            res.json({
                success: true,
                requirements: inMemoryRequirements,
                stats: getStatistics(inMemoryRequirements)
            });
        }
    } catch (error) {
        console.error('Error fetching requirements:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 添加需求
app.post('/api/add_requirement', async (req, res) => {
    try {
        const requirement = {
            title: (req.body.title || '').trim(),
            description: (req.body.description || '').trim(),
            priority: req.body.priority || '中',
            status: req.body.status || 'draft',
            owner: (req.body.owner || '').trim(),
            business_owner: (req.body.business_owner || '').trim(),
            project: (req.body.project || '').trim(),
            req_date: req.body.req_date || '',
            mrd_link: (req.body.mrd_link || '').trim(),
            prd_link: (req.body.prd_link || '').trim(),
            link: (req.body.link || '').trim(),
            created_date: new Date().toISOString(),
            updated_date: null
        };
        
        if (!requirement.title) {
            return res.status(400).json({
                success: false,
                error: '缺少需求标题'
            });
        }
        
        if (supabase) {
            const { data, error } = await supabase
                .from('requirements')
                .insert([requirement])
                .select();
            
            if (error) throw error;
            
            res.json({
                success: true,
                id: data[0].id,
                message: `需求 #${data[0].id} 添加成功`
            });
        } else {
            requirement.id = inMemoryRequirements.length + 1;
            inMemoryRequirements.push(requirement);
            
            res.json({
                success: true,
                id: requirement.id,
                message: `需求添加成功`
            });
        }
    } catch (error) {
        console.error('Error adding requirement:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 更新需求
app.put('/api/update_requirement/:id', async (req, res) => {
    try {
        const reqId = parseInt(req.params.id);
        const updates = req.body;
        
        if (supabase) {
            const { data, error } = await supabase
                .from('requirements')
                .update({
                    ...updates,
                    updated_date: new Date().toISOString()
                })
                .eq('id', reqId)
                .select();
            
            if (error) throw error;
            
            if (data.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: '需求不存在'
                });
            }
            
            res.json({
                success: true,
                message: `需求 #${reqId} 已更新`
            });
        } else {
            const index = inMemoryRequirements.findIndex(r => r.id === reqId);
            if (index === -1) {
                return res.status(404).json({
                    success: false,
                    error: '需求不存在'
                });
            }
            
            inMemoryRequirements[index] = {
                ...inMemoryRequirements[index],
                ...updates,
                updated_date: new Date().toISOString()
            };
            
            res.json({
                success: true,
                message: `需求 #${reqId} 已更新`
            });
        }
    } catch (error) {
        console.error('Error updating requirement:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 删除需求
app.delete('/api/delete_requirement/:id', async (req, res) => {
    try {
        const reqId = parseInt(req.params.id);
        
        if (supabase) {
            const { error } = await supabase
                .from('requirements')
                .delete()
                .eq('id', reqId);
            
            if (error) throw error;
            
            res.json({
                success: true,
                message: `需求 #${reqId} 已删除`
            });
        } else {
            const index = inMemoryRequirements.findIndex(r => r.id === reqId);
            if (index === -1) {
                return res.status(404).json({
                    success: false,
                    error: '需求不存在'
                });
            }
            
            inMemoryRequirements.splice(index, 1);
            
            res.json({
                success: true,
                message: `需求 #${reqId} 已删除`
            });
        }
    } catch (error) {
        console.error('Error deleting requirement:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 辅助函数：统计数据
function getStatistics(requirements) {
    const stats = { total: requirements.length };
    ['draft', 'review', 'approved', 'developing', 'completed'].forEach(status => {
        stats[status] = requirements.filter(r => r.status === status).length;
    });
    return stats;
}

// Vercel 部署：导出模块
module.exports = app;

// 本地开发：直接启动服务器
if (process.env.NODE_ENV !== 'production') {
    app.listen(PORT, () => {
        console.log('='.repeat(60));
        console.log('🚀 需求管理系统 - 多人协作版');
        console.log('='.repeat(60));
        console.log();
        console.log(`✅ 服务器运行在端口 ${PORT}`);
        console.log(`📡 访问地址：http://localhost:${PORT}`);
        console.log();
        console.log(supabase ? '✅ 已连接 Supabase 数据库（数据永久保存）' : '⚠️  使用内存存储（重启后数据丢失）');
        console.log();
        console.log('💡 提示：按 Ctrl+C 停止服务器');
        console.log('='.repeat(60));
    });
}
