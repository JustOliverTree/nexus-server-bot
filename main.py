import os
import json
import discord
from discord import option
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # <- Đọc biến môi trường

TOKEN = os.getenv("TOKEN")  # <- Token ẩn, an toàn

# ======================== Khởi tạo Bot ========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Bot(intents=intents)

# ======================== Cấu hình chung ========================
DATA_FILE = "data.json"

LEVEL_ROLES = {
    1: "🍼 Người Mới",
    5: "🧑‍🌾 Công Dân Mới",
    10: "🏅 Công Dân Kiểu Mẫu",
    20: "🏘️ Cư Dân Kỳ Cựu",
    30: "🎖️ Hội Viên Danh Dự",
    50: "⚔️ Hiệp Sĩ Ảo",
    70: "🧙‍♂️ Lão Làng",
    90: "👑 Tinh Anh Server",
    100: "🚀 Người Bảo Trợ Vũ Trụ"
}

XP_PER_CHAT = 5
XP_PER_CHECKIN = 10
COIN_PER_CHECKIN = 5

# force deploy render

# ======================== CẤU HÌNH XP THEO ROLE ========================
ROLE_XP_BONUS = {
    "Người Mới": 0,
    "Công Dân Mới": 1,
    "Công Dân Kiểu Mẫu": 2,
    "Cư Dân Kỳ Cựu": 3,
    "Hội Viên Danh Dự": 5
}

LEVEL_ROLES = {
    1: "Người Mới",
    5: "Công Dân Mới",
    10: "Công Dân Kiểu Mẫu",
    20: "Cư Dân Kỳ Cựu",
    30: "Hội Viên Danh Dự"
}

XP_PER_CHAT = 1  # điểm cơ bản mỗi tin nhắn

def xp_to_next_level(level):
    """Tính số XP cần để lên cấp tiếp theo"""
    multiplier = (level // 10) + 1
    return 100 * multiplier

def add_xp(member, base_xp):
    """Cộng XP cho người dùng, tự xử lý lên level"""
    user_id = str(member.id)

    if user_id not in user_data:
        user_data[user_id] = {
            "xp": 0,
            "level": 1,
            "coins": 0,
            "last_checkin": ""
        }

    # Tính bonus theo role
    bonus = 0
    for role in member.roles:
        if role.name in ROLE_XP_BONUS:
            bonus = max(bonus, ROLE_XP_BONUS[role.name])

    gained_xp = base_xp + bonus
    user_data[user_id]["xp"] += gained_xp

    current_level = user_data[user_id]["level"]

    # Kiểm tra lên cấp
    level_up = False
    while user_data[user_id]["xp"] >= xp_to_next_level(current_level):
        user_data[user_id]["xp"] -= xp_to_next_level(current_level)
        current_level += 1
        level_up = True

    user_data[user_id]["level"] = current_level
    save_data(user_data)

    return current_level if level_up else None



# ======================== Load và lưu dữ liệu ========================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ Lỗi JSON trong data.json! Reset về rỗng.")
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 💡 Load user_data chỉ 1 lần ở đây
user_data = load_data()

def add_coin(member, amount):
    data = load_data()
    user_id = str(member.id)
    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 0, "coins": 0, "last_checkin": ""}
    data[user_id]["coins"] += amount
    save_data(data)

# ======================== Sự kiện khi bot sẵn sàng ========================
@bot.event
async def on_ready():
    print(f"🤖 Bot đã sẵn sàng dưới tên: {bot.user}")

# ======================== /diem-danh ========================
@bot.slash_command(name="diem-danh", description="Điểm danh mỗi ngày để nhận XP và Tinh Thạch")
async def diem_danh(ctx):
    user_id = str(ctx.author.id)
    now = datetime.now().date()

    if user_id not in user_data:
        user_data[user_id] = {
            "xp": 0,
            "level": 1,
            "coins": 0,
            "last_checkin": ""
        }

    last_checkin_str = user_data[user_id].get("last_checkin", "")
    last_checkin = datetime.strptime(last_checkin_str, "%Y-%m-%d").date() if last_checkin_str else None

    if last_checkin == now:
        await ctx.respond("📅 Bạn đã điểm danh hôm nay rồi! Hãy quay lại vào ngày mai!", ephemeral=True)
        return

    # Cập nhật ngày điểm danh
    user_data[user_id]["last_checkin"] = str(now)
    user_data[user_id]["coins"] += COIN_PER_CHECKIN

    # Cộng XP khi điểm danh
    level_up = add_xp(ctx.author, XP_PER_CHECKIN)

    save_data(user_data)

    msg = f"✅ {ctx.author.mention} đã điểm danh và nhận được **{XP_PER_CHECKIN} XP** cùng **{COIN_PER_CHECKIN} Tinh Thạch**!"
    if level_up:
        role_name = LEVEL_ROLES.get(level_up)
        if role_name:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                await ctx.author.add_roles(role)
                msg += f"\n🎉 Bạn đã lên cấp **{level_up}** và nhận được vai trò **{role_name}**!"
            else:
                msg += f"\n🎉 Bạn đã lên cấp **{level_up}**!"
        else:
            msg += f"\n🎉 Bạn đã lên cấp **{level_up}**!"

    await ctx.respond(msg, ephemeral=True)

@bot.slash_command(name="xp", description="Xem hồ sơ level, XP và coin của bạn hoặc người khác")
async def xp(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)

    # Nếu người dùng chưa có dữ liệu thì tạo mới
    if user_id not in user_data:
        user_data[user_id] = {
            "xp": 0,
            "level": 1,
            "coins": 0,
            "last_checkin": ""
        }

    # Lấy thông tin
    data = user_data[user_id]
    level = data["level"]
    xp = data["xp"]
    coins = data["coins"]
    next_xp = xp_to_next_level(level)
    percent = int((xp / next_xp) * 100)

    # Tạo thanh tiến độ XP bằng ký tự
    filled = "█" * (percent // 10)
    empty = "░" * (10 - (percent // 10))
    bar = f"{filled}{empty} {xp}/{next_xp} XP"

    # Lấy role cấp độ (nếu có)
    role = None
    for r in member.roles[::-1]:  # Duyệt từ role cao nhất
        if r.name in ROLE_XP_BONUS:
            role = r.name
            break

    # Embed kết quả
    embed = discord.Embed(
        title=f"Hồ sơ của {member.display_name}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="🎖️ Cấp độ", value=f"Level {level}", inline=True)
    embed.add_field(name="💎 Tinh Thạch", value=f"{coins}", inline=True)
    embed.add_field(name="🏷️ Vai trò", value=role or "Không có", inline=True)
    embed.add_field(name="🌟 XP", value=bar, inline=False)

    await ctx.respond(embed=embed, ephemeral=True)


# ======================== /thong-bao ========================
@bot.slash_command(name="thong-bao", description="Gửi thông báo vào kênh 📣・announcements")
@option("tieude", description="Tiêu đề của thông báo")
@option("noidung", description="Nội dung muốn gửi")
@option("ping", description="Ping mọi người không?", choices=["Không ping", "@everyone", "@🎮 Minecraft"], required=False)
async def thong_bao(ctx: discord.ApplicationContext, tieude: str, noidung: str, ping: str = "Không ping"):
    allowed_roles = ["Admin", "Quản Trị Viên", "Quản Lý"]
    member_roles = [role.name for role in ctx.author.roles]

    if not ctx.author.guild_permissions.administrator and not any(role in allowed_roles for role in member_roles):
        await ctx.respond("❌ Bạn không có quyền dùng lệnh này!", ephemeral=True)
        return

    announcement_channel = discord.utils.get(ctx.guild.text_channels, name="📣・announcements")
    if announcement_channel is None:
        await ctx.respond("❌ Không tìm thấy kênh 📣・announcements!", ephemeral=True)
        return

    ping_text = ""
    if ping == "@everyone":
        ping_text = "@everyone"
    elif ping == "@🎮 Minecraft":
        ping_text = "<@&1392331132397162606>"

    embed = discord.Embed(title=tieude, description=noidung, color=0x00ffff)
    embed.set_footer(text=f"Người gửi: {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await announcement_channel.send(content=ping_text or None, embed=embed)
    await ctx.respond("✅ Thông báo đã được gửi!", ephemeral=True)

# ======================== /gop-y ========================
class GopYModal(discord.ui.Modal):
    def __init__(self, user):
        super().__init__(title="Góp ý cho server")
        self.user = user
        self.add_item(discord.ui.InputText(label="Nội dung góp ý", placeholder="Nhập ý kiến...", style=discord.InputTextStyle.paragraph, max_length=1000))

    async def callback(self, interaction: discord.Interaction):
        ykien = self.children[0].value

        embed_public = discord.Embed(title="📬 Góp ý mới", description=f"**{self.user.mention} đã gửi một góp ý:**\n\n{ykien}", color=discord.Color.green())
        embed_public.set_footer(text="Cảm ơn bạn đã đóng góp!", icon_url=self.user.avatar.url if self.user.avatar else None)

        embed_log = discord.Embed(title="📌 Góp ý được gửi", description=f"Từ: {self.user.name} ({self.user.id})\nNội dung:\n{ykien}", color=discord.Color.orange())

        congkhai = discord.utils.get(interaction.guild.text_channels, name="✉・gop-y")
        adminlog = discord.utils.get(interaction.guild.text_channels, name="📌・admin-log")

        if congkhai:
            await congkhai.send(embed=embed_public)
        if adminlog:
            await adminlog.send(embed=embed_log)

        await interaction.response.send_message("✅ Góp ý của bạn đã được gửi thành công!", ephemeral=True)

class GopYView(discord.ui.View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="📝 Góp ý", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Chỉ người dùng slash command mới có thể bấm!", ephemeral=True)
            return
        await interaction.response.send_modal(GopYModal(self.user))

@bot.slash_command(name="gop-y", description="Gửi góp ý cho server")
async def gop_y(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="📮 Góp ý cho server",
        description="Bạn có góp ý hoặc ý tưởng cho server? Hãy nhấn nút **📝 Góp ý** bên dưới để gửi!",
        color=discord.Color.blue()
    )
    view = GopYView(ctx.author)
    await ctx.respond(embed=embed, view=view, ephemeral=True)

# ======================== /thong-bao-mc ========================
class MCModal(discord.ui.Modal):
    def __init__(self, user):
        super().__init__(title="Tạo thông báo Minecraft")
        self.user = user
        self.add_item(discord.ui.InputText(label="Tiêu đề thông báo", placeholder="VD: Mở server lúc 20h30"))
        self.add_item(discord.ui.InputText(label="Thời gian mở", placeholder="VD: 9/7 lúc 20h30"))
        self.add_item(discord.ui.InputText(label="Nội dung chi tiết", style=discord.InputTextStyle.paragraph, placeholder="Thông tin server, mini game, thể lệ..."))

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        time = self.children[1].value
        desc = self.children[2].value

        embed = discord.Embed(
            title=f"🎮 {title}",
            description=f"🕒 **Thời gian mở:** {time}\n\n📋 **Chi tiết:**\n{desc}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Người gửi: {self.user.display_name}", icon_url=self.user.avatar.url if self.user.avatar else None)

        schedule_channel = discord.utils.get(interaction.guild.text_channels, name="📅・event-schedule")
        adminlog = discord.utils.get(interaction.guild.text_channels, name="📌・admin-log")

        ping_role = "<@&1392331132397162606>"  # ID role Minecraft

        if schedule_channel:
            await schedule_channel.send(content=ping_role, embed=embed)
        if adminlog:
            await adminlog.send(embed=embed)

        await interaction.response.send_message("✅ Thông báo Minecraft đã được gửi!", ephemeral=True)

class MCView(discord.ui.View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="📢 Tạo thông báo Minecraft", style=discord.ButtonStyle.success)
    async def button_callback(self, button, interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Chỉ người dùng slash command mới có thể bấm!", ephemeral=True)
            return
        await interaction.response.send_modal(MCModal(self.user))

@bot.slash_command(name="thong-bao-mc", description="Gửi thông báo mở server Minecraft")
async def thong_bao_mc(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="📅 Tạo thông báo Minecraft",
        description="Ấn nút bên dưới để bắt đầu gửi thông báo về sự kiện Minecraft!",
        color=discord.Color.orange()
    )
    view = MCView(ctx.author)
    await ctx.respond(embed=embed, view=view, ephemeral=True)

# ======================== /to-cao ========================
class ReportModal(discord.ui.Modal):
    def __init__(self, reporter, reported_user):
        super().__init__(title="Tố cáo người dùng")
        self.reporter = reporter
        self.reported_user = reported_user
        self.add_item(discord.ui.InputText(label="Lý do tố cáo", placeholder="Nhập lý do bạn muốn tố cáo người này...", style=discord.InputTextStyle.paragraph, max_length=1000))

    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value

        embed = discord.Embed(
            title="🚨 Tố cáo mới",
            description=f"**Người báo cáo:** {self.reporter.mention}\n**Người bị tố cáo:** {self.reported_user.mention}\n**Lý do:**\n{reason}",
            color=discord.Color.red()
        )
        embed.set_footer(text="Hệ thống quản lí server")

        adminlog = discord.utils.get(interaction.guild.text_channels, name="📌・admin-log")
        if adminlog:
            await adminlog.send(embed=embed)

        await interaction.response.send_message("✅ Tố cáo đã được gửi đến ban quản trị!", ephemeral=True)

class ReportView(discord.ui.View):
    def __init__(self, reporter):
        super().__init__()
        self.reporter = reporter

        self.user_select = discord.ui.UserSelect(placeholder="Chọn người bạn muốn tố cáo...")
        self.user_select.callback = self.select_callback
        self.add_item(self.user_select)

    async def select_callback(self, interaction: discord.Interaction):
        reported_user = self.user_select.values[0]
        if interaction.user != self.reporter:
            await interaction.response.send_message("❌ Bạn không thể chọn thay người khác!", ephemeral=True)
            return
        await interaction.response.send_modal(ReportModal(self.reporter, reported_user))

@bot.slash_command(name="to-cao", description="Tố cáo một người dùng")
async def to_cao(ctx: discord.ApplicationContext):
    view = ReportView(ctx.author)
    embed = discord.Embed(
        title="🛑 Tố cáo người dùng",
        description="Chọn người bạn muốn tố cáo bằng menu bên dưới.",
        color=discord.Color.red()
    )
    await ctx.respond(embed=embed, view=view, ephemeral=True)

# ======================== Welcome / Goodbye ========================
@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="👋・welcome")
    if welcome_channel:
        embed = discord.Embed(
            title="🎉 Thành viên mới!",
            description=f"Chào mừng {member.mention} đã gia nhập **{member.guild.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="📜 Nhớ đọc luật", value="<#📜・rules>", inline=True)
        embed.add_field(name="🎭 Nhận vai trò", value="<#📩・nhận-role>", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Thành viên thứ {member.guild.member_count} của server")
        await welcome_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    goodbye_channel = discord.utils.get(member.guild.text_channels, name="👋・goodbye")
    if goodbye_channel:
        embed = discord.Embed(
            title="👋 Một người vừa rời đi...",
            description=f"{member.display_name} đã rời khỏi server.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await goodbye_channel.send(embed=embed)

# ======================== XP khi chat ========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    level_up = add_xp(message.author, XP_PER_CHAT)
    if level_up:
        role_name = LEVEL_ROLES.get(level_up)
        if role_name:
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role:
                try:
                    await message.author.add_roles(role)
                    await message.channel.send(
                        f"🎉 {message.author.mention} đã lên cấp **{level_up}** và nhận được role **{role_name}**!"
                    )
                except discord.Forbidden:
                    await message.channel.send("❌ Bot không có quyền thêm role! Hãy cấp quyền `Manage Roles` và đảm bảo vai trò bot cao hơn role cần gán.")
            else:
                await message.channel.send(f"⚠️ Không tìm thấy role **{role_name}** trong server. Kiểm tra lại tên role trong `LEVEL_ROLES`!")
        else:
            await message.channel.send(f"✨ {message.author.mention} đã lên cấp **{level_up}**!")
    
    await bot.process_application_commands(message)

# ======================== /leaderboard ========================
@bot.slash_command(name="leaderboard", description="Xem bảng xếp hạng XP của server")
async def leaderboard(ctx: discord.ApplicationContext):
    await ctx.defer()  # Nếu server đông thì việc load có thể mất vài giây

    guild = ctx.guild
    members = guild.members

    # Tạo danh sách người dùng có trong user_data và là thành viên server
    valid_users = []
    for uid, info in user_data.items():
        member = guild.get_member(int(uid))
        if member:
            valid_users.append((member, info["xp"], info["level"]))

    # Sắp xếp theo XP giảm dần
    sorted_users = sorted(valid_users, key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 Bảng Xếp Hạng XP",
        description="Top những người tích cực nhất server!",
        color=discord.Color.purple()
    )

    for i, (member, xp, level) in enumerate(sorted_users[:10], start=1):
        embed.add_field(
            name=f"#{i} – {member.display_name}",
            value=f"Level: **{level}** | XP: `{xp}`",
            inline=False
        )

    # Nếu người dùng không nằm trong top 10 → hiển thị vị trí của họ
    current_user_id = str(ctx.author.id)
    user_rank = next((i for i, (m, _, _) in enumerate(sorted_users) if m.id == ctx.author.id), None)

    if user_rank is not None and user_rank >= 10:
        _, xp, level = sorted_users[user_rank]
        embed.add_field(
            name="📍 Vị trí của bạn",
            value=f"#{user_rank + 1} – {ctx.author.display_name}\nLevel: **{level}** | XP: `{xp}`",
            inline=False
        )

    await ctx.respond(embed=embed, ephemeral=True)

# ======================== Run bot ========================
bot.run(TOKEN)