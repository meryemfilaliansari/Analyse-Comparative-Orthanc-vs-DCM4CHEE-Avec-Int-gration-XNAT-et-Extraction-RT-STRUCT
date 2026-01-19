"""
Script pour afficher le schéma de la base de données PostgreSQL
"""
import psycopg2
from tabulate import tabulate

# Connexion à PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="pacs_db",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("SCHÉMA BASE DE DONNÉES - PACS COMPARISON PROJECT")
    print("="*80 + "\n")
    
    # Liste des tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    print(f"📊 Tables trouvées : {len(tables)}")
    print("-" * 80)
    
    for (table_name,) in tables:
        print(f"\n🗃️  TABLE: {table_name.upper()}")
        print("-" * 80)
        
        # Structure de la table
        cur.execute(f"""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        
        table_data = []
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            max_len = f"({col[2]})" if col[2] else ""
            nullable = "NULL" if col[3] == "YES" else "NOT NULL"
            default = col[4] if col[4] else ""
            
            table_data.append([
                col_name,
                f"{col_type}{max_len}",
                nullable,
                default[:40] if default else "-"
            ])
        
        print(tabulate(table_data, 
                      headers=["Colonne", "Type", "Nullable", "Défaut"],
                      tablefmt="grid"))
        
        # Contraintes et index
        cur.execute(f"""
            SELECT 
                conname as constraint_name,
                contype as constraint_type
            FROM pg_constraint
            WHERE conrelid = '{table_name}'::regclass;
        """)
        
        constraints = cur.fetchall()
        if constraints:
            print(f"\n🔑 Contraintes:")
            for const in constraints:
                const_type = {
                    'p': 'PRIMARY KEY',
                    'f': 'FOREIGN KEY',
                    'u': 'UNIQUE',
                    'c': 'CHECK'
                }.get(const[1], const[1])
                print(f"   • {const[0]} ({const_type})")
        
        # Nombre de lignes
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"\n📈 Nombre de lignes: {count}")
    
    print("\n" + "="*80)
    print("✅ Schéma affiché avec succès!")
    print("="*80 + "\n")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\nEssayez avec les identifiants par défaut:")
    print("  Host: localhost")
    print("  Port: 5432")
    print("  Database: pacs_db")
    print("  User: postgres")
    print("  Password: postgres")
