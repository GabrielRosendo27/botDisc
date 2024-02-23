import discord
import requests
import sqlite3
import time
import re
from discord.ext import commands
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

def iniciar_webdriver():
    service = Service(executable_path='C:\\Users\\Pichau\\Documents\\Arquivos\\Faculdade\\appBot\\chromedriver.exe')
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') 
    driver = webdriver.Chrome(service=service, options=options)
    return driver
# BANCO DE DADOS // 
# Conecta ao banco de dados (isso criará um novo arquivo players.db se não existir)
banco = sqlite3.connect('players.db')
cursor = banco.cursor()

# Função para adicionar um personagem ao banco de dados
def adicionar_personagem(player_name, player_vocation, player_level, player_guild_el, player_status_el):
                cursor.execute("INSERT INTO players (name, vocation, level, guild, status) VALUES (?, ?, ?, ?, ?)", (player_name, player_vocation, player_level, player_guild_el, player_status_el))
                banco.commit()
# Função para remover um personagem do banco de dados
def remover_personagem(nome_personagem):
                conn = sqlite3.connect('players.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM players WHERE name = ?", (nome_personagem,))
                conn.commit()
                conn.close()
# TRACKEANDO EM TEMPO REAL DB
                

# obtendo nome dos players do db                
cursor.execute("SELECT name FROM players")
resultados = cursor.fetchall()

for resultado in resultados: 
     nome_do_jogador = resultado[0]
     print(nome_do_jogador)
# starta o webdriver
driver = iniciar_webdriver()
driver.get('https://rubinot.com.br/?subtopic=characters')
for resultado in resultados: 
    nome_do_jogador = resultado[0]
    print(nome_do_jogador)
    time.sleep(4)
    # PEGANDO O PLAYER_NAME E NAVEGANDO NO SITE 
    driver.get('https://rubinot.com.br/?subtopic=characters')
    try:
        # Aguardar até que o input esteja visível e interagível
        player_name_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.NAME, 'name'))
        )
        player_name_input.clear()
        player_name_input.send_keys(nome_do_jogador)
        
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]'))
        )
        send_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div[2]/div[1]/div[2]/div/div[5]/div/div/div[1]/div/div/div/div'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
            
        player_level = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(4) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(4) > td:nth-child(2)').get_text()
        print(player_level)
       
        player_last_death = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(6) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(1) > td:nth-child(2)') 
        if player_last_death:
            player_l_death = player_last_death.get_text() 
        else: "Sem mortes"
        print(player_l_death)
        
        player_status = soup.find(style=re.compile(r'color:\s*green'))
        if player_status:
             player_l_status = "Online"
        else: "Offline"
        print(player_status)

        
    except TimeoutException:
        print("Personagem não encontrado.")

# DISCORD CONFIG //
intents = discord.Intents.all()
intents.messages = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)


# WEB SCRAPPING DADOS DB DISCORD
@client.event
async def on_message(message):
    print(f'Mensagem recebida: {message.content.strip()}')
    if message.author == client.user:
        return

    if message.content.startswith('!add'):
         # Divide a mensagem em palavras separadas
        words = message.content.split()
        # Verifica se há pelo menos duas palavras na mensagem (comando '!add' e nome do personagem)
        if len(words) >= 2:
            # O nome do personagem é a segunda palavra na mensagem
            player_name = ' '.join(words[1:])
            print(f"Comando !add detectado. Nome do personagem: {player_name}")
            # PEGANDO O PLAYER_NAME E NAVEGANDO NO SITE 
            # Configuração inicial do WebDriver
            driver = iniciar_webdriver()
            driver.get('https://rubinot.com.br/?subtopic=characters')
            player_name_input = driver.find_element(By.NAME, 'name')
            player_name_input.send_keys(player_name)    
            send_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
            send_button.click()
            try: 
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div/div[2]/div[1]/div[2]/div/div[5]/div/div/div[1]/div/div/div/div')))
            except TimeoutException:
                await message.channel.send("Personagem não encontrado.")
                
                if 'driver' in locals():
                    driver.quit()

            # BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            player_name = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(4) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(1) > td:nth-child(2) > span > b').get_text()

            player_vocation = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(4) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(3) > td:nth-child(2)').get_text()
            
            player_level = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(4) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(4) > td:nth-child(2)').get_text()
            
            
            player_guild = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(4) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(7) > td:nth-child(2) > a')
            
            if player_guild is not None:
                player_guild_el = player_guild.get_text()
            else: 
                player_guild_el = "Não possui Guild"
            
            
            player_status = soup.select_one('#characters > div.Border_2 > div > div > div:nth-child(8) > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(2) > td:nth-child(3) > b > span')
            
            if player_status is not None:
                player_status_el = player_status.get_text()
            else: 
                player_status_el = "Offline"
          
            adicionar_personagem(player_name, player_vocation, player_level, player_guild_el, player_status_el)



            await message.channel.send(player_name)
            await message.channel.send(player_vocation)
            await message.channel.send(player_level)
            await message.channel.send(player_guild_el)
            await message.channel.send(player_status_el)
            
            if 'driver' in locals():
              driver.quit()

    # INICIO WEB SCRAPPING //
    if message.content.strip().startswith('!loot'):
        print('Comando !loot detectado...')
        try:
            # Configuração do WebDriver (certifique-se de especificar o caminho para o seu driver)
            print('Iniciando o WebDriver...')
            driver = iniciar_webdriver()
            print('WebDriver iniciado com sucesso.')
            # Navegar até a página da web
            print('Navegando até a página da web...')
            driver.get('https://rubinot.com.br/?subtopic=killstatistics')
            print('Página da web carregada.')

            # Localizar o elemento select e selecionar a opção desejada
            print('Selecionando opção...')
            select_element = Select(driver.find_element(By.TAG_NAME, 'select'))
            select_element.select_by_value('0') 
            print('Opção selecionada com sucesso.')

            # Localizar e clicar no botão 'BigButton'
            print('Clicando no botão...')
            button = driver.find_element(By.CLASS_NAME, 'BigButtonText')
            driver.execute_script("arguments[0].click();", button)
            print('Botão clicado.')

            # Aguardar um tempo para a página carregar completamente após o clique no botão
            print('Aguardando a página carregar...')
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'TableContent')))  # Aguarda até que um elemento desejado apareça na página (substitua 'elemento_desejado' pelo ID real do elemento)
            print('Página carregada completamente.')

          # INICIO COLETA E TRATAMENTO DE DADOS COM BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            first_item = soup.select_one('#killstatistics > div.Border_2 > div > div > div > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(1) > td:nth-child(3)').get_text()
            second_item = soup.select_one('#killstatistics > div.Border_2 > div > div > div > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(2) > td:nth-child(3)').get_text()
            third_item = soup.select_one('#killstatistics > div.Border_2 > div > div > div > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(3) > td:nth-child(3)').get_text()
            fourth_item = soup.select_one('#killstatistics > div.Border_2 > div > div > div > table > tbody > tr > td > div > table > tbody > tr > td > div > table > tbody > tr:nth-child(4) > td:nth-child(3)').get_text()
            await message.channel.send(first_item)
            await message.channel.send(second_item)
            await message.channel.send(third_item)
            await message.channel.send(fourth_item)
        
        except Exception as e:
            error_message = f"Ocorreu um erro: {e}"
            print(error_message)
            channel = message.channel
            await channel.send(error_message)

        finally:
            # Fechar o navegador
            if 'driver' in locals():
              driver.quit()

# Comando para remover um personagem do banco de dados
    if message.content.startswith('!remove'):
        # Divide a mensagem em palavras separadas
        words = message.content.split()
        # Verifica se há pelo menos duas palavras na mensagem (comando '!remove' e nome do personagem)
        if len(words) >= 2:
            # O nome do personagem é a segunda palavra na mensagem
            nome_personagem = ' '.join(words[1:])
            # Convertendo o nome do personagem para letras minúsculas
            nome_personagem = nome_personagem.lower()
            # Verifica se o personagem existe no banco de dados, considerando letras minúsculas
            cursor.execute("SELECT * FROM players WHERE LOWER(name) = ?", (nome_personagem,))
            result = cursor.fetchone()
            # Se o personagem existir, remova-o do banco de dados
            if result:
                remover_personagem(result[0])  # Remover personagem pelo ID
                await message.channel.send(f"Personagem {nome_personagem} removido do banco de dados.")
            else:
                await message.channel.send(f"Personagem {nome_personagem} não encontrado no banco de dados.")

# Substitua 'TOKEN_DO_SEU_BOT' pelo token real do seu bot
client.run('')
