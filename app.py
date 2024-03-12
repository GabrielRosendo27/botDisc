import discord
import sqlite3
import re
import asyncio
from discord import TextChannel
from discord.utils import get
from discord import Embed
from discord.ext import commands
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

intents = discord.Intents.all()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

banco = sqlite3.connect('players.db')
cursor = banco.cursor()

def remover_personagem(player_id): 
    cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
    banco.commit()

def iniciar_webdriver(): 
    service = Service(executable_path='C:\\Users\\Pichau\\Documents\\Arquivos\\Faculdade\\botDisc\\chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    driver = webdriver.Chrome(service=service, options=options)
    return driver

async def track_players(bot: commands.Bot, channel_id: int):
    driver = iniciar_webdriver()
    driver.get('https://rubinot.com.br/?subtopic=characters')
    old_player_data = {}
    cursor.execute("SELECT MAX(id) FROM players")
    max_player_id = cursor.fetchone()[0]
    processed_players = 0
    while True:
        cursor.execute("SELECT name FROM players")
        player_names = [row[0] for row in cursor.fetchall()]
        for player_name in player_names:
            print(f"Rastreando jogador ------------> {player_name}")
            try:
                driver.get('https://rubinot.com.br/?subtopic=characters')
                await asyncio.sleep(3)
                player_name_input = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.NAME, 'name'))
                )
                player_name_input.clear()
                player_name_input.send_keys(player_name)
                
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]'))
                )
                send_button.click()
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div[2]/div[1]/div[2]/div/div[5]/div/div/div[1]/div/div/div/div'))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
    
                level_text = soup.find('td', string='Level:')
                if level_text:
                    player_level = level_text.find_next_sibling('td').get_text(strip=True)
                    print(player_level)
                
                player_status = soup.find('span', style='color: green') is not None
                if player_status:
                    player_status = "Online"
                else:
                    player_status = "Offline"
                print(player_status)


                def is_death_td(tag):
                    return tag.name == 'td' and re.search(r'Killed at level \d+ by', tag.get_text())
                
                death_text_td = soup.find(is_death_td)
                if death_text_td:
                    #player_death = death_text_td.get_text(strip=True)
                    player_death = re.search(r'Killed at level \d+ by .*', death_text_td.get_text()).group()
                else:
                    player_death = "Sem Mortes"
                print("PLAYER DEATH -------------------------- ", player_death)

                cursor.execute("UPDATE players SET level=?, last_death=?, status=? WHERE name=?", (player_level, player_death, player_status, player_name))
                banco.commit()
                print('Dados atualizados no banco de dados')
                processed_players += 1
                print("MAX PLAYER ID --> ",max_player_id)
                print("Número de player processados --> ",processed_players)
                await asyncio.sleep(5)
            except TimeoutException:
                    print(f"Personagem {player_name} não encontrado.")  
            for player_name in player_names:
                cursor.execute("SELECT level, last_death, status FROM players WHERE name=?", (player_name,))
                new_player_data = cursor.fetchone()
                if new_player_data:
                    old_level, old_last_death, old_status = old_player_data.get(player_name, (None, None, None))
                    new_level, new_last_death, new_status = new_player_data
                    if processed_players >= max_player_id:
                        print("------------ INFORMAÇÕES ATUALIZADAS ------------")
                        if new_level != old_level:
                            await send_message(bot, channel_id, f"```asciidoc\n'{player_name}' Level: `{old_level}` para `{new_level}` :: \n```")     

                        if new_status != old_status:
                            await send_message(bot, channel_id, f"""```asciidoc\n._'{player_name}' ficou '{new_status}'\n```""")
                                                    
                        if new_last_death != old_last_death:
                            await send_message(bot, channel_id, f"""```fix\n{player_name} - {new_last_death}.\n```""") 
                    old_player_data[player_name] = new_player_data           
                else:
                    print(f"Não foi possível recuperar os dados do jogador {player_name}")
                        

async def send_message(bot: commands.Bot, channel_id: int, message: str):
    channel: TextChannel = get(bot.get_all_channels(), id=channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"Canal com ID {channel_id} não encontrado.")

@bot.event
async def on_ready():
    print('Iniciando bot Discord...')
    channel_id = 1213211328592748605  # Substitua pelo ID real do canal
    bot.loop.create_task(track_players(bot, channel_id))

@bot.command()
async def add(ctx, *, player_name):
    print(f"Comando !add detectado. Nome do personagem: {player_name}")
    player_name_lower = player_name.lower()
    cursor.execute("SELECT * FROM players WHERE LOWER(name) = ?", (player_name_lower,))
    existing_player = cursor.fetchone()
    print("checando se jogador existe no banco de dados...")
    if existing_player:
        await ctx.send("Este personagem já existe no banco de dados.")
        return
    driver = iniciar_webdriver()
    driver.get('https://rubinot.com.br/?subtopic=characters')
    player_name_input = driver.find_element(By.NAME, 'name')
    player_name_input.send_keys(player_name)    
    send_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
    send_button.click()
    print("botao clicado...")
    try: 
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div[2]/div[1]/div[2]/div/div[5]/div/div/div[1]/div/div/div/div')))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print('coletando dados...')

        player_text = soup.find('td', string='Name:')
        if player_text:
            player_name = player_text.find_next_sibling('td').get_text(strip=True)
            player_name = re.sub(r'\(.*\)', '', player_name).strip()
            print(player_name)
        else:
            print("Nome não encontrado.")

        vocation_text = soup.find('td', string='Vocation:')
        if vocation_text:
            player_vocation = vocation_text.find_next_sibling('td').get_text(strip=True)
            print(player_vocation)

        level_text = soup.find('td', string='Level:')
        if level_text:
            player_level = level_text.find_next_sibling('td').get_text(strip=True)
            print(player_level)

        guild_text = soup.find('td', string='Guild:')
        if guild_text:
            player_guild = guild_text.find_next_sibling('td').get_text()
            print(player_guild)
        else:
            player_guild = ("Sem Guild")

        player_status = soup.find('span', style='color: green') is not None
        if player_status:
            player_status = "Online"
        else:
            player_status = "Offline"
        print(player_status)

        cursor.execute("INSERT INTO players (name, vocation, level, guild, status) VALUES (?, ?, ?, ?, ?)", (player_name, player_vocation, player_level, player_guild, player_status))
        banco.commit()
        print("inserido!")
        embed = Embed(
            title="Informações do jogador",
            description=f"Nome: {player_name}\nVocação: {player_vocation}\nLevel: {player_level}\nGuild: {player_guild}\nStatus: {player_status}\nAdicionado ao banco de dados.",
            color=0x0000FF)
        await ctx.send(embed=embed)
    except TimeoutException:
        await ctx.send("Personagem não encontrado.")
    finally:
        if 'driver' in locals():
            driver.quit()

@bot.command()
async def remove(ctx, *, nome_personagem):
    nome_personagem = nome_personagem.lower()
    cursor.execute("SELECT id FROM players WHERE LOWER(name) = ?", (nome_personagem,))
    result = cursor.fetchone()
    if result:
        remover_personagem(result[0])
        await ctx.send(f"Personagem {nome_personagem} removido do banco de dados.")
    else:
        await ctx.send(f"Personagem {nome_personagem} não encontrado no banco de dados.")

bot.run('TokenDoBot')
