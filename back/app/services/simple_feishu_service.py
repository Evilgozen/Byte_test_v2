import os
import json
from dotenv import load_dotenv
import lark_oapi as lark
from lark_oapi.api.auth.v3 import *
from lark_oapi.api.docx.v1 import *

# 加载环境变量
load_dotenv()

class SimpleFeishuService:
    """
    简化的飞书文档服务类，只提供基本的创建文档和添加内容功能
    基于 test_feishu_lark_sdk.py 中的实现
    """
    
    def __init__(self):
        # 从环境变量获取配置
        self.app_id = os.getenv('FEISHU_APP_ID')
        self.app_secret = os.getenv('FEISHU_APP_SECRET')
        
        if not self.app_id or not self.app_secret:
            raise ValueError("请在.env文件中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
        
        # 创建client
        self.client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()
    
    def get_access_token(self):
        """
        获取飞书应用访问令牌
        """
        try:
            # 构造请求对象
            request = InternalTenantAccessTokenRequest.builder() \
                .request_body(InternalTenantAccessTokenRequestBody.builder()
                    .app_id(self.app_id)
                    .app_secret(self.app_secret)
                    .build()) \
                .build()
            
            # 发起请求
            response = self.client.auth.v3.tenant_access_token.internal(request)
            
            # 处理失败返回
            if not response.success():
                raise Exception(f"获取token失败: {response.msg}")
            
            # 提取token信息
            if response.raw and response.raw.content:
                content_data = json.loads(response.raw.content)
                if 'tenant_access_token' in content_data:
                    return content_data['tenant_access_token']
                else:
                    raise Exception("响应中没有tenant_access_token字段")
            else:
                raise Exception("响应中没有内容")
                
        except Exception as e:
            raise Exception(f"获取访问令牌失败: {str(e)}")
    
    def create_document(self, title):
        """
        创建飞书文档
        
        Args:
            title: 文档标题
        
        Returns:
            文档ID，如果创建失败返回None
        """
        try:
            # 构造创建文档请求
            request = CreateDocumentRequest.builder() \
                .request_body(CreateDocumentRequestBody.builder()
                    .title(title)
                    .build()) \
                .build()
            
            # 发起请求
            response = self.client.docx.v1.document.create(request)
            
            # 处理失败返回
            if not response.success():
                raise Exception(f"创建文档失败: {response.msg}")
            
            # 检查响应对象结构
            if hasattr(response, 'data') and hasattr(response.data, 'document'):
                doc = response.data.document
                if hasattr(doc, 'document_id'):
                    return doc.document_id
            
            raise Exception("无法从响应中获取文档ID")
            
        except Exception as e:
            raise Exception(f"创建文档失败: {str(e)}")
    
    def get_document_blocks(self, document_id):
        """
        获取文档的块列表
        
        Args:
            document_id: 文档ID
        
        Returns:
            第一个块的ID，用于后续添加内容
        """
        try:
            # 构造请求对象
            request = ListDocumentBlockRequest.builder() \
                .document_id(document_id) \
                .page_size(500) \
                .document_revision_id(-1) \
                .build()
            
            # 发起请求
            response = self.client.docx.v1.document_block.list(request)
            
            # 处理失败返回
            if not response.success():
                raise Exception(f"获取块列表失败: {response.msg}")
            
            # 返回第一个块的ID作为父块ID
            if hasattr(response, 'data') and hasattr(response.data, 'items') and response.data.items:
                first_block = response.data.items[0]
                if hasattr(first_block, 'block_id'):
                    return first_block.block_id
            
            # 如果没有找到块，返回文档ID
            return document_id
            
        except Exception as e:
            # 如果获取块列表失败，返回文档ID作为默认值
            return document_id
    
    def add_content_to_document(self, document_id, content):
        """
        向文档添加文本内容
        
        Args:
            document_id: 文档ID
            content: 要添加的文本内容
        
        Returns:
            是否添加成功
        """
        try:
            # 获取文档的块ID
            block_id = self.get_document_blocks(document_id)
            
            # 构造添加内容请求
            text_request = CreateDocumentBlockChildrenRequest.builder() \
                .document_id(document_id) \
                .block_id(block_id) \
                .document_revision_id(-1) \
                .request_body(CreateDocumentBlockChildrenRequestBody.builder()
                    .children([
                        Block.builder()
                        .block_type(2)  # 文本块类型
                        .text(Text.builder()
                            .style(TextStyle.builder().build())
                            .elements([
                                TextElement.builder()
                                .text_run(TextRun.builder()
                                    .content(content)
                                    .text_element_style(TextElementStyle.builder()
                                        .build())
                                    .build())
                                .build()
                            ])
                            .build())
                        .build()
                    ])
                    .index(0)
                    .build()) \
                .build()
            
            # 发起请求
            response = self.client.docx.v1.document_block_children.create(text_request)
            
            if response.success():
                return True
            else:
                raise Exception(f"添加内容失败: {response.msg}")
                
        except Exception as e:
            raise Exception(f"添加内容失败: {str(e)}")
    
    def create_document_with_content(self, title, content):
        """
        创建文档并添加内容的便捷方法
        
        Args:
            title: 文档标题
            content: 文档内容
        
        Returns:
            dict: 包含文档ID和操作结果的字典
        """
        try:
            # 创建文档
            document_id = self.create_document(title)
            if not document_id:
                raise Exception("创建文档失败")
            
            # 添加内容
            success = self.add_content_to_document(document_id, content)
            if not success:
                raise Exception("添加内容失败")
            
            return {
                "success": True,
                "document_id": document_id,
                "document_url": f"https://bytedance.feishu.cn/docx/{document_id}",
                "message": "文档创建并添加内容成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"操作失败: {str(e)}"
            }