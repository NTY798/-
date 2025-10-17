# try'.py 最终修正版本
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import time
import base64
from pathlib import Path
import streamlit.components.v1 as components

# ======================================================================
# --- 阿里云 OSS 存储配置 START ---
# ⚠️ 注意：API 连接必须使用 Streamlit Secrets 中配置的 Endpoint（现在我们知道应该是北京）

try:
    import oss2

    # ⚠️ 从 Streamlit Secrets 中读取配置 (请确保 Streamlit Cloud Secrets 已配置为北京 Endpoint！)
    OSS_BUCKET_NAME = st.secrets["oss_config"]["BUCKET_NAME"]
    OSS_ENDPOINT = st.secrets["oss_config"]["ENDPOINT"]  # 应该为 oss-cn-beijing.aliyuncs.com
    OSS_ACCESS_KEY_ID = st.secrets["oss_config"]["ACCESS_KEY_ID"]
    OSS_ACCESS_KEY_SECRET = st.secrets["oss_config"]["ACCESS_KEY_SECRET"]

    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    oss_available = True


    # OSS上传函数
    def upload_to_oss(uploaded_file, folder="uploads/"):
        file_name = f"{folder}{uploaded_file.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}{Path(uploaded_file.name).suffix}"
        file_bytes = uploaded_file.getvalue()

        # 核心修复点：此时 bucket 必须使用北京 Endpoint 才能 put_object 成功
        bucket.put_object(file_name, file_bytes)

        # 返回公共访问 URL（使用北京的公共 URL，这与您的所有图片URL保持一致）
        # ⚠️ 注意：我们在这里硬编码了北京的公共读 URL，因为所有图片都在那里
        return f"https://{OSS_BUCKET_NAME}.oss-cn-beijing.aliyuncs.com/{file_name}"

except ImportError:
    st.error("未找到 'oss2' 库。请运行 pip install oss2 安装。")
    oss_available = False
except Exception as e:
    # 提示用户检查 Secrets 配置
    st.error(
        f"❌ OSS 连接失败：请确保 Streamlit Secrets 中配置了 [oss_config] 且 ENDPOINT 为 oss-cn-beijing.aliyuncs.com。错误信息: {e}")
    oss_available = False
# --- 阿里云 OSS 存储配置 END ---


# --- 页面配置 (修复 page_icon) ---
# 使用表情符号，避免云端路径问题
try:
    st.set_page_config(
        page_title="津沽水哨兵 | 津水守护者",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    st.error(f"页面配置错误：{e}")

# 统一使用您提供的 **北京 OSS URL 基础** 作为图片显示链接
BASE_IMAGE_URL = "https://nty798.oss-cn-beijing.aliyuncs.com/"

# --- 1. 数据结构模拟 ---
# 之前动态生成 BASE_OSS_URL 的代码已移除，使用固定的 BASE_IMAGE_URL
# BASE_OSS_URL = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT.split('//')[-1]}/" # <-- 移除此行，避免混乱

if 'issues' not in st.session_state:
    st.session_state.issues = pd.DataFrame(
        {
            "ID": [1001, 1002, 1003],
            "时间": [datetime(2025, 10, 10, 14, 30), datetime(2025, 10, 9, 9, 0), datetime(2025, 10, 8, 11, 0)],
            "河段": ["海河 (大光明桥段)", "子牙河 (红桥区段)", "永定新河"],
            "问题类型": ["固体垃圾堆积", "生活污水直排", "水面油污"],
            "描述": ["岸边发现大量塑料瓶和外卖盒", "排污口有白色泡沫和异味", "水面可见片状油污"],
            "Status": ["待认领", "已认领", "已解决"],
            "用户ID": ["u001", "u002", "u001"],
            "积分奖励": [50, 80, 70],
            "image_url": [
                f"{BASE_IMAGE_URL}demage.png",
                f"{BASE_IMAGE_URL}eye.png",
                f"{BASE_IMAGE_URL}bird.png"
            ],
            "认领人": ["牛天原", "郄家航", "杨凯升"],
            "解决奖励": [100, 150, 300]
        }
    )

if 'user_points' not in st.session_state:
    st.session_state.user_points = 350
    st.session_state.user_name = "天津卫守护者"


# --- 2. 界面布局：侧边栏与主区域 ---
def app_sidebar():
    """侧边栏：用户信息和导航"""
    with st.sidebar:
        # 使用 BASE_IMAGE_URL 加载 a.ico
        st.image(f"{BASE_IMAGE_URL}a.ico", use_container_width=True, caption="津沽水哨兵 LOGO")
        st.title("🌊 津沽水哨兵")

        st.markdown(f"**欢迎，{st.session_state.user_name}！**")
        st.info(f"🏅 **当前积分：{st.session_state.user_points}**")

        st.subheader("功能导航")
        menu = st.radio(
            "请选择功能",
            ["📸 随手拍上报", "🗺️ 精准志愿行", "💡 津水知识库", "🎁 积分商城/兑换"],
            index=0,
            key="app_menu"
        )
        return menu


# --- 3. 核心功能模块 ---

# --- 3.1 随手拍问题上报 ---
def render_issue_reporting():
    """渲染“随手拍”问题上报页面"""
    st.header("📸 随手拍问题上报")
    st.markdown("---")

    # 检查OSS是否可用
    if not oss_available:
        st.error("由于OSS配置问题，问题上报和文件上传功能被禁用。请检查 Streamlit Secrets 配置！")

    st.subheader("环境问题快速上报")

    with st.form("issue_report_form"):
        st.warning("⚠️ **已自动定位至：天津市，请选择关联河段。**")
        river_segment = st.selectbox(
            "🏷️ 关联河段标签",
            ["海河 (大光明桥段)", "子牙河 (红桥区段)", "永定新河", "其他/不确定"]
        )

        issue_type = st.multiselect(
            "🚨 问题类型（可多选）",
            ["生活污水直排", "工业废水偷排", "固体垃圾堆积", "水面油污", "其他污染"],
            default=["固体垃圾堆积"]
        )

        description = st.text_area("详细描述（如气味、颜色、规模等）", max_chars=300)

        uploaded_file = st.file_uploader("📷 上传现场照片/视频", type=['png', 'jpg', 'jpeg', 'mp4'],
                                         accept_multiple_files=False, disabled=not oss_available)  # 无法连接OSS则禁用上传

        submit_button = st.form_submit_button("✅ 提交问题，同步至'虚拟河长'后台", disabled=not oss_available)

        if submit_button:
            if not uploaded_file or not description:
                st.error("请上传图片并填写描述！")
            else:
                # 实际上传到 OSS 并获取真实 URL
                with st.spinner('正在上传照片到云端...'):
                    # 只有 OSS 可用时才调用上传
                    real_url = upload_to_oss(uploaded_file)

                new_id = st.session_state.issues['ID'].max() + 1
                points_report = random.choice([50, 60, 80])
                points_solve = random.choice([100, 120, 150])

                new_issue = {
                    "ID": new_id,
                    "时间": datetime.now(),
                    "河段": river_segment,
                    "问题类型": ", ".join(issue_type),
                    "描述": description[:50] + "...",
                    "Status": "待认领",
                    "用户ID": st.session_state.user_name,
                    "积分奖励": points_report,
                    "image_url": real_url,
                    "认领人": "",
                    "解决奖励": points_solve
                }

                st.session_state.issues.loc[len(st.session_state.issues)] = new_issue
                st.session_state.user_points += points_report

                st.success(f"🎉 **上报成功！** 问题ID: {new_id}。已奖励 **{points_report}** 积分！感谢您的贡献。")
                st.balloons()
                st.rerun()

    st.markdown("---")
    st.subheader("📢 待认领/已上报问题公开列表 (数据共享)")
    st.caption("以下列表展示了所有用户上报的问题记录，供'精准志愿行'认领。")

    display_issues = st.session_state.issues.sort_values(by="时间", ascending=False).copy()
    df_to_display = display_issues[['时间', '河段', '问题类型', 'Status', '积分奖励', '认领人', '解决奖励']]

    st.dataframe(
        df_to_display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Status": st.column_config.Column("问题状态", help="待认领的问题可被志愿行接取"),
            "积分奖励": st.column_config.NumberColumn("上报奖励", format="🏅%d"),
            "解决奖励": st.column_config.NumberColumn("志愿行奖励", format="💰%d")
        }
    )


# --- 3.2 精准志愿行：解决问题 ---
def render_volunteer_actions():
    """渲染“精准志愿行”任务页面 (解决上报的问题)"""
    st.header("🗺️ 精准志愿行")
    st.markdown("---")
    st.subheader("待认领问题列表 (您的行动入口)")

    if not oss_available:
        st.warning("由于OSS配置问题，文件上传功能受限，部分功能可能无法使用。")

    available_issues = st.session_state.issues[st.session_state.issues['Status'] == '待认领'].sort_values(by="时间",
                                                                                                          ascending=True)

    if available_issues.empty:
        st.success("🎉 当前所有上报问题均已被认领或解决！感谢河海卫士的努力！")
        return

    for index, issue in available_issues.iterrows():
        with st.expander(f"✨ 问题ID {issue['ID']}：{issue['河段']} - 奖励 {issue['解决奖励']} 积分", expanded=True):
            st.markdown(f"**🚨 问题类型:** {issue['问题类型']}")
            st.markdown(f"**📝 上报描述:** {issue['描述']}")
            st.markdown(f"**⏳ 上报时间:** {issue['时间'].strftime('%Y-%m-%d %H:%M')}")
            st.info(f"💰 **解决此问题可获得奖励：{issue['解决奖励']} 积分**")

            # 展示照片：使用 BASE_IMAGE_URL
            st.image(issue['image_url'], caption=f"上报人拍摄的原问题照片 (ID:{issue['ID']})", width=300)

            # 认领和解决表单
            with st.form(f"solve_form_{issue['ID']}"):
                st.subheader(f"📍 认领并提交解决报告")

                solution_report = st.text_area("您采取的解决措施和结果（至少50字）")

                solved_photos = st.file_uploader("📷 上传问题已解决的现场照片 (至少1张)", accept_multiple_files=True,
                                                 key=f"solved_upload_{issue['ID']}", disabled=not oss_available)

                if st.form_submit_button(f"✅ 提交解决报告并申请积分 (问题ID {issue['ID']})",
                                         disabled=not oss_available):
                    if len(solution_report) < 50 or not solved_photos:
                        st.error("请提供解决措施和至少一张解决后的照片！")
                    else:
                        st.session_state.issues.loc[index, 'Status'] = '审核中'
                        st.session_state.issues.loc[index, '认领人'] = st.session_state.user_name

                        reward = issue['解决奖励']
                        st.session_state.user_points += reward

                        st.success(
                            f"✅ 解决报告已提交！问题ID {issue['ID']} 状态更新为'审核中'。**{reward}** 积分已预发放到您的账户。")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()


# --- 3.3 津水知识库 ---
def render_knowledge_base():
    """渲染“津水知识库”页面"""
    st.header("💡 津水知识库")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["💧 治理案例", "🦢 本地水鸟识别", "🔬 科学解读"])

    with tab1:
        st.subheader("天津河海治理案例")
        st.markdown("**子牙河'加减乘除'治污法**")
        st.write(
            "📖 '加'**生态补水，**'减'**排污总量，**'乘'**科技手段，**'除'黑臭水体。通过系统性工程，子牙河水质得到显著提升。")

        # 使用 B站 HTML 嵌入方式
        bilibili_html_embed_1 = """
        <iframe src="//player.bilibili.com/player.html?bvid=BV1pg411o7Uz&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="width: 100%; height: 350px;"> </iframe>
        """
        components.html(bilibili_html_embed_1, height=360)
        st.markdown("---")

        st.markdown("**水下森林系统**")
        st.write("🍃 运用沉水植物构建水下生态系统，通过净化水体、抑制藻类生长，实现水质自净。")

        bilibili_html_embed_2 = """
        <iframe src="//player.bilibili.com/player.html?bvid=BV14v4y137sC&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="width: 100%; height: 350px;"> </iframe>
        """
        components.html(bilibili_html_embed_2, height=360)

    with tab2:
        st.subheader("天津本地水鸟识别指南")
        st.markdown("**回归子牙河的'白鹭'和'野鸭'**")
        col1, col2 = st.columns(2)
        with col1:
            st.image(f"{BASE_IMAGE_URL}bird.png", caption="小白鹭 (常见于海河子牙河交汇处)")
            st.write("🔍 **识别小贴士：** 白鹭体态优雅，羽毛洁白")
        with col2:
            st.image(f"{BASE_IMAGE_URL}duck.png", caption="绿头鸭 (常见于湿地和水库)")
            st.write("🔍 **识别小贴士：** 野鸭多为深色，头部有金属光泽。水鸟的回归是水环境改善最直观的指标！")

    with tab3:
        st.subheader("专业内容短视频/漫画解读")
        st.markdown("## 漫画解读：雨污混接点的危害")
        st.image(f"{BASE_IMAGE_URL}demage.png", caption="一图看懂混接的危害和治理必要性")
        st.write("📢 专业知识不复杂！用通俗易懂的方式了解治水原理。")


# --- 3.4 积分激励体系 ---
def render_point_system():
    """渲染“积分商城/兑换”页面"""
    st.header("🎁 积分商城与激励体系")
    st.markdown("---")

    st.info(f"🏅 **您的可用积分：{st.session_state.user_points}**")

    st.subheader("🛍️ 兑换天津特色环保文创")

    items = [
        {"名称": "🌊 空气加湿器", "积分": 500, "描述": "感受海风迎面的氤氲气息",
         "image": f"{BASE_IMAGE_URL}cup.png"},
        {"名称": "📚 随机毛绒玩具", "积分": 300, "描述": "可爱毛绒玩具，抚慰一天疲惫心灵",
         "image": f"{BASE_IMAGE_URL}toy.png"},
        {"名称": "🌳 健康院文创布包", "积分": 100, "描述": "印有健康院专属图案，河工学子IP文创",
         "image": f"{BASE_IMAGE_URL}bag.png"}
    ]

    for item in items:
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            st.image(item['image'])
        with col2:
            st.markdown(f"**{item['名称']}**")
            st.caption(item['描述'])
        with col3:
            st.warning(f"需 {item['积分']} 积分")
        with col4:
            can_buy = st.session_state.user_points >= item['积分']
            if st.button("兑换", disabled=not can_buy, key=f"buy_{item['名称']}"):
                st.session_state.user_points -= item['积分']
                st.success(f"✅ 兑换成功！'{item['名称']}' 将在3个工作日内寄出。")
                st.rerun()

    st.markdown("---")
    st.subheader("💚 积分捐赠：支持河道生态补水")

    donation_amount = st.number_input("请输入您想捐赠的积分数量", min_value=10, max_value=st.session_state.user_points,
                                      step=10, key="donate_input")

    if st.button("💰 捐赠积分支持生态补水"):
        if donation_amount > st.session_state.user_points:
            st.error("积分不足，请重新输入！")
        else:
            st.session_state.user_points -= donation_amount
            st.success(f"🙏 感谢您捐赠 **{donation_amount}** 积分！它们将用于支持海河、子牙河等河道的生态补水项目。")
            st.rerun()


# --- 4. 主运行逻辑 ---
def main():
    """主函数：根据侧边栏选择渲染对应模块"""
    selected_menu = app_sidebar()

    st.markdown("<style>section[data-testid='stSidebar'] {background-color: #e0f7fa;}</style>",
                unsafe_allow_html=True)
    st.markdown("<style>h1, h2, h3 {color: #00796b;}</style>", unsafe_allow_html=True)

    if selected_menu == "📸 随手拍上报":
        render_issue_reporting()
    elif selected_menu == "🗺️ 精准志愿行":
        render_volunteer_actions()
    elif selected_menu == "💡 津水知识库":
        render_knowledge_base()
    elif selected_menu == "🎁 积分商城/兑换":
        render_point_system()


if __name__ == "__main__":
    main()
