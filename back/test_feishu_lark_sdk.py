import json
import os
from dotenv import load_dotenv
import lark_oapi as lark
from lark_oapi.api.auth.v3 import *
from lark_oapi.api.docx.v1 import *

# 加载环境变量
load_dotenv()

def test_lark_sdk_token():
    """使用lark-oapi SDK测试获取token"""
    print("🚀 使用lark-oapi SDK测试获取token...")
    print("=" * 50)
    
    # 从环境变量获取配置
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ 请在.env文件中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
        return None
    
    print(f"📱 App ID: {app_id}")
    print(f"🔑 App Secret: {app_secret[:10]}...")
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        print("✅ 客户端创建成功")
        
        # 构造请求对象
        request = InternalTenantAccessTokenRequest.builder() \
            .request_body(InternalTenantAccessTokenRequestBody.builder()
                .app_id(app_id)
                .app_secret(app_secret)
                .build()) \
            .build()
        
        print("✅ 请求对象构造成功")
        
        # 发起请求
        response = client.auth.v3.tenant_access_token.internal(request)
        
        # 处理失败返回
        if not response.success():
            print(f"❌ 获取token失败:")
            print(f"   错误码: {response.code}")
            print(f"   错误信息: {response.msg}")
            print(f"   Log ID: {response.get_log_id()}")
            if response.raw and response.raw.content:
                try:
                    error_detail = json.loads(response.raw.content)
                    print(f"   详细错误: {json.dumps(error_detail, indent=4, ensure_ascii=False)}")
                except:
                    print(f"   原始响应: {response.raw.content}")
            return None
        
        # 处理业务结果
        print("✅ 成功获取token!")
        print(f"📄 Token响应: {lark.JSON.marshal(response, indent=4)}")
        
        # 提取token信息 - 从raw.content解析JSON
        if response.raw and response.raw.content:
            try:
                content_data = json.loads(response.raw.content)
                if 'tenant_access_token' in content_data:
                    token = content_data['tenant_access_token']
                    expire = content_data.get('expire', 'Unknown')
                    print(f"🎯 Token: {token[:20]}...")
                    print(f"⏰ 过期时间: {expire} 秒")
                    return token
                else:
                    print("❌ 响应中没有tenant_access_token字段")
                    print(f"📋 响应内容: {content_data}")
                    return None
            except json.JSONDecodeError as e:
                print(f"❌ 解析响应JSON失败: {e}")
                print(f"📋 原始内容: {response.raw.content}")
                return None
        else:
            print("❌ 响应中没有内容")
            return None
            
    except Exception as e:
        print(f"❌ 发生异常: {type(e).__name__}: {e}")
        import traceback
        print(f"📋 详细错误信息:")
        traceback.print_exc()
        return None

def test_lark_sdk_create_document(token):
    """使用lark-oapi SDK测试创建文档"""
    if not token:
        print("❌ 没有有效的token，无法创建文档")
        return None
    
    print("\n📋 使用lark-oapi SDK测试创建文档...")
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        # 构造创建文档请求
        request = CreateDocumentRequest.builder() \
            .request_body(CreateDocumentRequestBody.builder()
                .title(f"SDK测试文档-{os.urandom(4).hex()}")
                .build()) \
            .build()
        
        # 发起请求
        response = client.docx.v1.document.create(request)
        
        # 处理失败返回
        if not response.success():
            print(f"❌ 创建文档失败:")
            print(f"   错误码: {response.code}")
            print(f"   错误信息: {response.msg}")
            print(f"   Log ID: {response.get_log_id()}")
            if response.raw and response.raw.content:
                try:
                    error_detail = json.loads(response.raw.content)
                    print(f"   详细错误: {json.dumps(error_detail, indent=4, ensure_ascii=False)}")
                except:
                    print(f"   原始响应: {response.raw.content}")
            return None
        
        # 处理业务结果
        print("✅ 成功创建文档!")
        print(f"📄 文档响应: {lark.JSON.marshal(response, indent=4)}")
        
        # 检查响应对象结构
        if hasattr(response, 'data') and hasattr(response.data, 'document'):
            doc = response.data.document
            if hasattr(doc, 'document_id'):
                print(f"📄 文档ID: {doc.document_id}")
                print(f"📝 文档标题: {getattr(doc, 'title', 'Unknown')}")
                return doc.document_id
        elif hasattr(response, 'document'):
            doc = response.document
            if hasattr(doc, 'document_id'):
                print(f"📄 文档ID: {doc.document_id}")
                print(f"📝 文档标题: {getattr(doc, 'title', 'Unknown')}")
                return doc.document_id
        else:
            print(f"📋 响应对象属性: {dir(response)}")
            if hasattr(response, 'data'):
                print(f"📋 data对象属性: {dir(response.data)}")
        
        return None
        
    except Exception as e:
        print(f"❌ 创建文档时发生异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_document_blocks(token, document_id):
    """获取文档的块列表"""
    if not token or not document_id:
        print("❌ 没有有效的token或文档ID，无法获取块列表")
        return None
    
    print("\n📋 获取文档块列表...")
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        # 构造请求对象
        request = ListDocumentBlockRequest.builder() \
            .document_id(document_id) \
            .page_size(500) \
            .document_revision_id(-1) \
            .build()
        
        # 发起请求
        response = client.docx.v1.document_block.list(request)
        
        # 处理失败返回
        if not response.success():
            print(f"❌ 获取块列表失败: {response.msg}")
            if response.raw and response.raw.content:
                try:
                    error_detail = json.loads(response.raw.content)
                    print(f"   详细错误: {json.dumps(error_detail, indent=4, ensure_ascii=False)}")
                except:
                    print(f"   原始响应: {response.raw.content}")
            return None
        
        # 处理业务结果
        print("✅ 成功获取块列表!")
        print(f"📄 块列表数据: {lark.JSON.marshal(response.data, indent=4)}")
        
        # 返回第一个块的ID作为父块ID
        if hasattr(response, 'data') and hasattr(response.data, 'items') and response.data.items:
            first_block = response.data.items[0]
            if hasattr(first_block, 'block_id'):
                print(f"📄 找到第一个块ID: {first_block.block_id}")
                return first_block.block_id
        
        return None
        
    except Exception as e:
        print(f"❌ 获取块列表时发生异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_lark_sdk_add_content(token, document_id):
    """使用lark-oapi SDK测试向文档添加内容"""
    if not token or not document_id:
        print("❌ 没有有效的token或文档ID，无法添加内容")
        return False
    
    print("\n📝 使用lark-oapi SDK测试向文档添加内容...")
    
    # 首先获取文档的块列表，找到可以插入的位置
    block_id = get_document_blocks(token, document_id)
    if not block_id:
        print("❌ 无法获取文档块ID，使用文档ID作为块ID")
        block_id = document_id
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        block_results = []
        
        # 1. 使用CreateDocumentBlockChildrenRequest添加文本块
        print("\n📄 添加文本块...")
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
                                .content("多人实时协同，插入一切元素。不仅是在线文档，更是")
                                .text_element_style(TextElementStyle.builder()
                                    .background_color(14)
                                    .text_color(5)
                                    .build())
                                .build())
                            .build(),
                            TextElement.builder()
                            .text_run(TextRun.builder()
                                .content("强大的创作和互动工具")
                                .text_element_style(TextElementStyle.builder()
                                    .bold(True)
                                    .background_color(14)
                                    .text_color(5)
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
        
        text_response = client.docx.v1.document_block_children.create(text_request)
        
        if text_response.success():
            print("✅ 文本块创建成功!")
            block_results.append("text")
            if hasattr(text_response, 'data'):
                print(f"📄 文本块数据: {lark.JSON.marshal(text_response.data, indent=4)}")
            else:
                print(f"📄 文本块响应: {lark.JSON.marshal(text_response, indent=4)}")
        else:
            print(f"❌ 文本块创建失败: {text_response.msg}")
            if text_response.raw and text_response.raw.content:
                try:
                    error_detail = json.loads(text_response.raw.content)
                    print(f"   详细错误: {json.dumps(error_detail, indent=4, ensure_ascii=False)}")
                except:
                    print(f"   原始响应: {text_response.raw.content}")
        
        return len(block_results) > 0
        
    except Exception as e:
        print(f"❌ 添加内容时发生异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_requests_method():
    """对比requests方法和SDK方法的差异"""
    print("\n" + "=" * 50)
    print("🔍 对比分析: requests vs lark-oapi SDK")
    print("=" * 50)
    
    print("\n📊 主要差异:")
    print("1. 依赖管理:")
    print("   - requests方法: 需要手动管理HTTP请求、错误处理")
    print("   - SDK方法: 封装了请求逻辑，提供类型安全")
    
    print("\n2. 错误处理:")
    print("   - requests方法: 需要手动解析HTTP状态码和响应")
    print("   - SDK方法: 提供统一的错误处理机制")
    
    print("\n3. 类型安全:")
    print("   - requests方法: 使用字典和JSON，容易出错")
    print("   - SDK方法: 强类型，IDE支持自动补全")
    
    print("\n4. 维护性:")
    print("   - requests方法: 需要跟踪API变更，手动更新")
    print("   - SDK方法: 官方维护，自动跟踪API变更")
    
    print("\n💡 建议:")
    print("   - 生产环境推荐使用lark-oapi SDK")
    print("   - 简单测试可以使用requests方法")
    print("   - SDK提供更好的错误处理和类型安全")

def main():
    """主测试函数"""
    print("🚀 飞书API测试 - lark-oapi SDK vs requests")
    print("=" * 60)
    
    # 测试SDK方法获取token
    token = test_lark_sdk_token()
    
    # 如果token获取成功，测试创建文档
    if token:
        document_id = test_lark_sdk_create_document(token)
        if document_id:
            # 测试添加内容块
            content_success = test_lark_sdk_add_content(token, document_id)
            if content_success:
                print(f"\n✅ 完整测试成功! 文档ID: {document_id}，内容添加成功")
            else:
                print(f"\n⚠️ 文档创建成功但内容添加失败! 文档ID: {document_id}")
        else:
            print("\n❌ 文档创建失败，跳过内容添加测试")
    else:
        print("\n❌ Token获取失败，跳过所有文档操作")
    
    # 对比分析
    compare_with_requests_method()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    
    # 提供问题排查建议
    print("\n🔧 如果遇到问题，请检查:")
    print("1. 网络连接是否正常")
    print("2. .env文件中的APP_ID和APP_SECRET是否正确")
    print("3. 飞书应用是否已启用并配置了正确的权限")
    print("4. lark-oapi包是否已正确安装: pip install lark-oapi")
    print("5. 查看控制台的详细错误信息")

if __name__ == "__main__":
    main()