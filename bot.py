#Read the README.md file before insert the code on your code

TICKETS_FILE = "tickets-server.txt"

# Fonction pour lire les configurations depuis le fichier
def read_ticket_config():
    if not os.path.exists(TICKETS_FILE):
        return {}
    
    configs = {}
    with open(TICKETS_FILE, 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) >= 4:
                server_id = int(parts[0])
                roles = parts[1:]
                configs[server_id] = roles
    return configs

# Fonction pour écrire les configurations dans le fichier
def write_ticket_config(configs):
    with open(TICKETS_FILE, 'w') as file:
        for server_id, roles in configs.items():
            file.write(f"{server_id}|{'|'.join(roles)}\n")

# Fonction pour obtenir la configuration pour un serveur spécifique
def get_server_config(server_id):
    configs = read_ticket_config()
    return configs.get(server_id, [])

# Fonction pour définir la configuration pour un serveur spécifique
def set_server_config(server_id, roles):
    configs = read_ticket_config()
    configs[server_id] = roles
    write_ticket_config(configs)

# Commande pour configurer le système de tickets
@bot.tree.command(name="ticket-configure", description="Configurer le système de tickets")
@app_commands.describe(
    category="La catégorie pour les tickets",
    role1="Rôle à mentionner lors de l'ouverture du ticket (optionnel)",
    role2="Deuxième rôle à mentionner lors de l'ouverture du ticket (optionnel)",
    role3="Troisième rôle à mentionner lors de l'ouverture du ticket (optionnel)",
)
async def configure(interaction: discord.Interaction, category: str = None, role1: discord.Role = None, role2: discord.Role = None, role3: discord.Role = None):
    # Vérifier si l'utilisateur a la permission de gérer le serveur
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Vous n'avez pas la permission de `gérer le serveur`.", ephemeral=True)
        return

    guild_id = interaction.guild.id
    roles = [role1.mention if role1 else '', role2.mention if role2 else '', role3.mention if role3 else '']

    # Mettre à jour la configuration pour ce serveur
    set_server_config(guild_id, roles)
    
    await interaction.response.send_message("Configuration mise à jour.", ephemeral=True)


# Commande pour ouvrir un ticket
@bot.tree.command(name="open-ticket", description="Ouvrir un ticket")
@app_commands.describe(reason="La raison de l'ouverture du ticket")
async def open_ticket(interaction: discord.Interaction, reason: str):
    guild = interaction.guild
    guild_id = guild.id
    roles_mentions = get_server_config(guild_id)

    category_name = "Tickets Abyss"
    embed_content = "Nouveau Ticket"

    # Créer ou obtenir la catégorie de tickets
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)

    # Vérifiez si un canal de ticket avec le même utilisateur existe déjà
    for channel in category.channels:
        if channel.name == f"ticket-{interaction.user.id}":
            await interaction.response.send_message("Vous avez déjà un ticket ouvert.", ephemeral=True)
            return

    # Crée le salon de ticket avec les permissions appropriées
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    for role in guild.roles:
        if role.permissions.manage_messages:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)

    ticket_channel = await category.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)

    # Créer un embed pour le message d'ouverture du ticket
    embed = discord.Embed(
        title=f"Nouveau Ticket ouvert par {interaction.user.name}",
        description=f"{interaction.user.mention} :  ```{reason}```",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Ticket créé par {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

    # Envoyer le message embed et mentionner les rôles ayant accès
    await ticket_channel.send(embed=embed)
    if roles_mentions:
        await ticket_channel.send(f"Mention des rôles : {' '.join(filter(None, roles_mentions))}")

    await interaction.response.send_message(f"Ticket créé: {ticket_channel.mention}", ephemeral=True)

# Commande pour fermer un ticket
@bot.tree.command(name="close-ticket", description="Fermer un ticket")
@app_commands.describe(reason="La raison de la fermeture du ticket")
async def close_ticket(interaction: discord.Interaction, reason: str):
        await interaction.response.send_message(f"Le ticket sera fermé pour la raison suivante : {reason}")
        await interaction.channel.delete()
