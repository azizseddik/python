import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':   os.getenv('DB_HOST', '127.0.0.1'),
    'port':   int(os.getenv('DB_PORT', '3306')),
    'user':   os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4',
}
DB_NAME = os.getenv('DB_NAME', 'bibliotheque_db')

LIVRES_INITIAUX = [
    ('Le Petit Prince',        'Antoine de Saint-Exupéry', 'Roman',        1943, 3, 'disponible'),
    ('Les Misérables',         'Victor Hugo',              'Roman',        1862, 0, 'emprunté'),
    ('Notre-Dame de Paris',    'Victor Hugo',              'Roman',        1831, 2, 'disponible'),
    ('Les Contemplations',     'Victor Hugo',              'Poésie',       1856, 1, 'disponible'),
    ('Orgueil et Préjugés',    'Jane Austen',              'Roman',        1813, 2, 'disponible'),
    ('Jane Eyre',              'Charlotte Brontë',         'Roman',        1847, 1, 'disponible'),
    ('Le Rouge et le Noir',    'Stendhal',                 'Roman',        1830, 0, 'emprunté'),
    ('1984',                   'George Orwell',            'Science',      1949, 2, 'disponible'),
    ('Sapiens',                'Yuval Noah Harari',        'Histoire',     2011, 3, 'disponible'),
    ('Python pour les Nuls',   'John Paul Mueller',        'Informatique', 2018, 1, 'disponible'),
    ('Dune',                   'Frank Herbert',            'Science',      1965, 2, 'réservé'),
    ('Le Comte de Monte-Cristo','Alexandre Dumas',         'Roman',        1844, 1, 'disponible'),
]


def _connect(**extra):
    return pymysql.connect(**DB_CONFIG, **extra)


def init_db():
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{DB_NAME}`")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS livres (
                    id_livre           INT AUTO_INCREMENT PRIMARY KEY,
                    titre              VARCHAR(255) NOT NULL,
                    auteur             VARCHAR(255) NOT NULL,
                    categorie          VARCHAR(100) DEFAULT '',
                    annee_publication  INT          DEFAULT NULL,
                    quantite_disponible INT         DEFAULT 0,
                    statut             ENUM('disponible','emprunté','réservé')
                                       DEFAULT 'disponible'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("SELECT COUNT(*) FROM livres")
            if cur.fetchone()[0] == 0:
                cur.executemany("""
                    INSERT INTO livres
                        (titre, auteur, categorie, annee_publication,
                         quantite_disponible, statut)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, LIVRES_INITIAUX)
        conn.commit()
    finally:
        conn.close()


def get_connection():
    return pymysql.connect(
        **DB_CONFIG,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_all_livres():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM livres ORDER BY id_livre")
            return cur.fetchall()


def get_livre_by_id(id_livre):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM livres WHERE id_livre = %s", (id_livre,))
            return cur.fetchone()


def search_livres(query):
    with get_connection() as conn:
        with conn.cursor() as cur:
            like = f"%{query}%"
            cur.execute("""
                SELECT * FROM livres
                WHERE titre LIKE %s
                   OR auteur LIKE %s
                   OR CAST(id_livre AS CHAR) = %s
                ORDER BY id_livre
            """, (like, like, query.strip()))
            return cur.fetchall()


def add_livre(titre, auteur, categorie, annee_publication, quantite_disponible, statut):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO livres
                    (titre, auteur, categorie, annee_publication,
                     quantite_disponible, statut)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (titre, auteur, categorie, annee_publication,
                  quantite_disponible, statut))
        conn.commit()
        return cur.lastrowid


def update_livre(id_livre, titre, auteur, categorie,
                 annee_publication, quantite_disponible, statut):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE livres
                SET titre=%s, auteur=%s, categorie=%s,
                    annee_publication=%s, quantite_disponible=%s, statut=%s
                WHERE id_livre=%s
            """, (titre, auteur, categorie, annee_publication,
                  quantite_disponible, statut, id_livre))
        conn.commit()


def delete_livre(id_livre):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM livres WHERE id_livre = %s", (id_livre,))
        conn.commit()
