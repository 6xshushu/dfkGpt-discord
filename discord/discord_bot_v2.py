import discord
import json
import aiohttp
from collections import defaultdict
from datetime import datetime, timedelta
from discord import Option

bot = discord.Bot( intents=discord.Intents.all())

# 存储用户的计数器和上次重置的时间
user_counter = defaultdict(int)
user_last_reset_time = defaultdict(datetime)

def extract_info(data):
    answer = data['answer']
    sources = [meta['metadata']['source'] for meta in data['meta']]
    source_list = sources
    source_list = list(set(source_list))
    combined_sources = '\n '.join(source_list)

    result = {
        "answer": answer,
        "source": combined_sources
    }
    return result


@bot.event
async def on_ready():
    print("DFK_GPT is online")


@bot.slash_command(name="ask", description="ask questions about DFK")
async def answer(ctx, question: str = Option(
        default="",
        description="The question you want to ask about DFK",
    )):
    user_id = ctx.author.id

    # 如果用户不在 user_last_reset_time 字典中，添加他们
    if user_id not in user_last_reset_time:
        user_last_reset_time[user_id] = datetime.now()

    # 检查是否需要重置用户的计数器
    if datetime.now() - user_last_reset_time[user_id] >= timedelta(hours=1):
        user_counter[user_id] = 0
        user_last_reset_time[user_id] = datetime.now()

    # 检查用户是否已达到每小时使用的限制
    if user_counter[user_id] >= 5:
        await ctx.respond("Sorry, you can only use this command five times per hour.",ephemeral=True)
    else:
        
        await ctx.defer()
        user_counter[user_id] += 1
        data = {'question': question}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('----api_url----/ask', data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        extracted_info = extract_info(result)

                        embed = discord.Embed(
                            title=question,
                            description=extracted_info["answer"],
                            color=discord.Colour.blurple(),
                        )
                        

                        embed.add_field(name="source", value=extracted_info["source"])

                        await ctx.send_followup(embed=embed)

                    else:
                        await ctx.send_followup('Failed to get answer')
        except aiohttp.ClientError as e:
            print(f"Client error: {e}")
            await ctx.send_followup('An unexpected error occurred while sending the request')
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            await ctx.send_followup('An unexpected error occurred while processing the response')
        except Exception as e:
            print(f"Unexpected error: {e}")
            await ctx.send_followup('An unexpected error occurred')

bot.run('------------your discord bot token------------')  # 请替换成你自己的 token