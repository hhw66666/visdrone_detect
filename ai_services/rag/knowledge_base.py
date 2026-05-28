# -*- coding: utf-8 -*-
"""
知识库初始化
为小科客服填充检测系统的使用知识
"""

from typing import List, Dict, Any


# 检测系统的知识文档
KNOWLEDGE_BASE_DOCS = [
    # ========== 基本介绍 ==========
    {
        "id": "intro_001",
        "content": "科大巡弋是一款基于 YOLOv8 深度学习模型的智能航拍目标检测系统。系统能够自动识别航拍图片和视频中的车辆、行人等目标，并提供详细的位置信息和统计报表。系统支持图片检测、视频检测、批量检测等多种模式。",
        "metadata": {"category": "系统介绍", "source": "系统文档"}
    },
    {
        "id": "intro_002",
        "content": "系统可以识别的目标类别包括：小汽车、摩托车、人群、行人、带篷三轮车、三轮车、自行车、卡车、面包车、公交车等 10 类目标。这些类别涵盖了常见的道路交通参与者和航拍场景中的主要对象。",
        "metadata": {"category": "目标类别", "source": "系统文档"}
    },

    # ========== 图片检测 ==========
    {
        "id": "img_001",
        "content": "进行图片检测的步骤：1. 登录系统后，点击顶部导航栏的「检测」按钮进入检测页面。2. 点击上传区域或直接拖拽图片到上传框。3. 系统支持 JPG、PNG、BMP 等常见图片格式。4. 调整置信度阈值（默认 0.25），置信度越高，检测框越少但越准确。5. 调整 IOU 阈值（默认 0.45），用于去除重叠的检测框。6. 点击「开始检测」按钮，等待几秒后查看结果。",
        "metadata": {"category": "图片检测", "source": "操作指南"}
    },
    {
        "id": "img_002",
        "content": "置信度阈值 conf_thres 的取值范围是 0.0 到 1.0。数值越高，表示只有置信度更高的目标才会被显示。例如设置为 0.5 时，只有置信度超过 50% 的检测结果才会显示。这有助于过滤掉低质量的检测框，减少误报。",
        "metadata": {"category": "图片检测", "source": "参数说明"}
    },
    {
        "id": "img_003",
        "content": "IOU 阈值 iou_thres 用于非极大值抑制（NMS）。当两个检测框的 IOU 超过此阈值时，系统会自动去除置信度较低的那个。默认值为 0.45。如果设置过低，可能会漏检；如果设置过高，可能会出现重复检测框。",
        "metadata": {"category": "图片检测", "source": "参数说明"}
    },

    # ========== 视频检测 ==========
    {
        "id": "video_001",
        "content": "进行视频检测的步骤：1. 在检测页面，选择「视频检测」标签。2. 点击上传按钮，选择视频文件。系统支持 MP4、AVI、MOV 等常见视频格式。3. 上传完成后，点击「开始检测」按钮。4. 系统会对视频进行逐帧分析，统计每一帧中的目标数量。5. 检测完成后，可以查看检测结果视频和统计数据。",
        "metadata": {"category": "视频检测", "source": "操作指南"}
    },
    {
        "id": "video_002",
        "content": "视频检测会对上传的视频文件进行逐帧分析。处理时间取决于视频长度和视频大小。一般来说，一分钟的高清视频大约需要 2-3 分钟处理时间。检测结果包括：每一帧的检测框标注、目标数量随时间变化的曲线图、各类目标的统计柱状图等。",
        "metadata": {"category": "视频检测", "source": "操作指南"}
    },

    # ========== 历史记录 ==========
    {
        "id": "history_001",
        "content": "查看历史记录的步骤：1. 点击顶部导航栏的「历史」按钮。2. 进入历史页面后，可以看到所有检测记录的列表。3. 每条记录显示：文件名、检测时间、检测类型（图片/视频）、检测到的目标数量。4. 点击任意记录可以查看详细的检测结果。5. 支持通过搜索框按文件名搜索记录。6. 支持按检测类型（图片/视频）进行筛选。",
        "metadata": {"category": "历史记录", "source": "操作指南"}
    },
    {
        "id": "history_002",
        "content": "历史记录页面支持分页显示，每页默认显示 12 条记录。可以通过页面底部的分页导航按钮查看更多记录。在记录详情页面，可以查看检测结果的详细信息，包括各个目标的类别、置信度和位置坐标。",
        "metadata": {"category": "历史记录", "source": "操作指南"}
    },

    # ========== 个人资料 ==========
    {
        "id": "profile_001",
        "content": "修改个人资料的步骤：1. 点击顶部导航栏的「我的」按钮。2. 进入个人资料页面。3. 可以修改用户名。4. 点击头像区域可以上传新的头像图片，支持 JPG、PNG、GIF 格式，图片大小不能超过 5MB。5. 修改完成后会自动保存。",
        "metadata": {"category": "个人资料", "source": "操作指南"}
    },

    # ========== 常见问题 ==========
    {
        "id": "faq_001",
        "content": "如果检测结果为空，可能的原因包括：1. 图片中没有系统能识别的 10 类目标。2. 置信度阈值设置过高，可以适当降低。3. 图片质量过低或目标过小。4. 图片中的目标被遮挡严重。解决方法：降低置信度阈值到 0.2 或 0.15，然后重新检测。",
        "metadata": {"category": "常见问题", "source": "故障排除"}
    },
    {
        "id": "faq_002",
        "content": "如果上传图片失败，请检查：1. 图片格式是否为系统支持的 JPG、PNG、BMP。2. 图片大小是否过大，建议不超过 10MB。3. 网络连接是否正常。4. 浏览器是否为最新版本，建议使用 Chrome 或 Firefox。",
        "metadata": {"category": "常见问题", "source": "故障排除"}
    },
    {
        "id": "faq_003",
        "content": "系统使用 GPU 加速进行目标检测，可以大幅提升检测速度。如果服务器有 NVIDIA 显卡且安装了 CUDA，系统会自动使用 GPU 进行加速。如果没有 GPU，系统会使用 CPU 进行检测，速度会慢一些。",
        "metadata": {"category": "常见问题", "source": "技术说明"}
    },

    # ========== 数据分析 ==========
    {
        "id": "data_001",
        "content": "检测结果页面会显示详细的统计数据：1. 总检测数：当前检测中识别出的所有目标数量。2. 类别分布：各类目标（车、人、自行车等）的数量柱状图。3. 置信度分布：检测结果的置信度分布情况。4. 位置热力图：目标在图片中的位置分布情况。",
        "metadata": {"category": "数据分析", "source": "功能说明"}
    },
]


def get_knowledge_base_docs() -> List[Dict[str, Any]]:
    """
    获取知识库文档

    Returns:
        知识库文档列表
    """
    return KNOWLEDGE_BASE_DOCS


def initialize_knowledge_base(retriever=None) -> int:
    """
    初始化知识库

    Args:
        retriever: Retriever 实例，如果为 None 则创建新的

    Returns:
        添加的文档数量
    """
    if retriever is None:
        from .retriever import get_retriever
        retriever = get_retriever()

    # 清空旧数据
    retriever.clear()

    # 添加知识文档
    docs = get_knowledge_base_docs()
    retriever.add_documents(docs)

    return len(docs)


def load_knowledge_base(
    persist_directory: str = None,
    collection_name: str = "xiaoyu_knowledge",
    embedder_type: str = "sentence_transformers",
) -> tuple:
    """
    加载知识库

    Args:
        persist_directory: 持久化目录
        collection_name: collection 名称
        embedder_type: 向量化器类型

    Returns:
        (retriever, doc_count): 检索器和文档数量
    """
    from .retriever import Retriever
    from .embedder import get_embedder

    retriever = Retriever(
        embedder=get_embedder(embedder_type),
        persist_directory=persist_directory,
        collection_name=collection_name,
        use_chroma=True,
    )

    doc_count = retriever.count()

    # 如果知识库为空，初始化
    if doc_count == 0:
        doc_count = initialize_knowledge_base(retriever)

    return retriever, doc_count
