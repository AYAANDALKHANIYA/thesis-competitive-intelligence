import os
import asyncio
import asyncpg

async def inspect_schema():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    # Get database version
    version = await conn.fetchval("SELECT version();")
    print(f"Database version: {version}")
    
    # Get tables in public schema
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    """)
    table_names = [t['table_name'] for t in tables]
    
    print("\nTABLES AND COLUMNS:")
    for t_name in table_names:
        print(f"\n--- Table: {t_name} ---")
        
        # Get columns
        columns = await conn.fetch(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, t_name)
        
        # Get primary keys
        pks = await conn.fetch(f"""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                 AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = $1::regclass
            AND    i.indisprimary
        """, t_name)
        pk_cols = [pk['attname'] for pk in pks]
        print(f"Primary Key(s): {', '.join(pk_cols)}")
        
        # Get foreign keys
        fks = await conn.fetch("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = $1
        """, t_name)
        
        fk_dict = {fk['column_name']: (fk['foreign_table_name'], fk['foreign_column_name']) for fk in fks}
        
        for col in columns:
            fk_info = f" -> {fk_dict[col['column_name']][0]}.{fk_dict[col['column_name']][1]}" if col['column_name'] in fk_dict else ""
            print(f"  {col['column_name']} ({col['data_type']}) {'NOT NULL' if col['is_nullable'] == 'NO' else ''}{fk_info}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(inspect_schema())
