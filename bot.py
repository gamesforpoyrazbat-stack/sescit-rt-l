import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web

# --- BOT VE SUNUCU AYARLARI ---
TOKEN = os.environ.get("DISCORD_TOKEN")  # Render Environment Variable
CHANNEL_ID = 1555639349163331647        # Ses kanalının ID'si
JOIN_ROLE_ID = 1555651923883855902       # Sunucuya girenlere verilecek ROLÜN ID'si

# --- INTENTS (Members Intent Zorunludur) ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True                  # Sunucuya katılanları tespit etmek için

bot = commands.Bot(command_prefix="!", intents=intents)

# --- RENDER KEEP-ALIVE (WEB SERVER) ---
async def handle_ping(request):
    return web.Response(text="Bot 7/24 Aktif!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/ping', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render'ın atadığı PORT değişkenini okur, varsayılan 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[WEB SERVER] {port} portunda sorunsuz başlatıldı.")

# --- SESSİZLİK (SILENCE) SES KAYNAĞI ---
# Discord'un botu "idle" sanıp atmasını önlemek için 20ms'lik sessiz Opus paketi gönderir
class SilenceAudio(discord.AudioSource):
    def read(self):
        return b'\xf8\xff\xfe'

# --- SES KANALINA BAĞLANMA FONKSİYONU ---
async def join_voice_channel():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel or not isinstance(channel, discord.VoiceChannel):
        print("Hata: Belirtilen ID'ye sahip geçerli bir ses kanalı bulunamadı.")
        return

    while not bot.is_closed():
        try:
            voice_client = discord.utils.get(bot.voice_clients, guild=channel.guild)
            
            # Bağlantı yoksa veya kopmuşsa
            if voice_client is None or not voice_client.is_connected():
                if voice_client is not None:
                    await voice_client.disconnect(force=True)
                
                vc = await channel.connect(reconnect=True, self_deaf=True)
                print(f"[{channel.guild.name}] - '{channel.name}' kanalına bağlandı.")
                
                if not vc.is_playing():
                    vc.play(SilenceAudio())
            
            # Bağlantı var ama sessiz paket durmuşsa tekrar başlat
            elif not voice_client.is_playing():
                voice_client.play(SilenceAudio())

        except Exception as e:
            print(f"Ses kanalına bağlanırken hata oluştu: {e}")
        
        await asyncio.sleep(15)

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"{bot.user.name} olarak başarıyla giriş yapıldı!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="7/24 Ses Modu"))

# Sunucuya yeni biri katıldığında çalışır
@bot.event
async def on_member_join(member):
    if member.bot:
        return
        
    role = member.guild.get_role(JOIN_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
            print(f"[OTO-ROL VERİLDİ] {member.display_name} kullanıcısına {role.name} rolü eklendi.")
        except Exception as e:
            print(f"Rol verilirken hata oluştu ({member.display_name}): {e}")
    else:
        print(f"Hata: {JOIN_ROLE_ID} ID'li rol bulunamadı.")

# --- ANA ÇALIŞTIRICI ---
async def main():
    async with bot:
        await start_web_server()
        bot.loop.create_task(join_voice_channel())
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())