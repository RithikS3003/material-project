# queries.py

# SQL queries for noun_value_mstr table
GENERATE_MODIFIER_ID = "SELECT noun_id FROM noun_value_mstr ORDER BY noun_id DESC LIMIT 1"


GET_NOUNS = """
    SELECT noun_id, noun, isActive, abbreviation, description
    FROM noun_value_mstr
    ORDER BY noun_id;
"""

GET_NOUN_BY_ID = """
    SELECT noun_id, noun, isActive, abbreviation, description
    FROM noun_value_mstr
    WHERE noun_id = :noun_id;
"""

CREATE_NOUN = """
    INSERT INTO noun_value_mstr (noun_id, noun, abbreviation, description, isActive)
    VALUES (:noun_id, :noun, :abbreviation, :description, :isActive)
    RETURNING noun_id, noun, abbreviation, description, isActive;
"""

UPDATE_NOUN = """
    UPDATE noun_value_mstr
    SET noun = :noun,
        abbreviation = :abbreviation,
        description = :description,
        isActive = :isActive
    WHERE noun_id = :noun_id
    RETURNING noun_id, noun, abbreviation, description, isActive;
"""

DELETE_NOUN = """
    DELETE FROM noun_value_mstr
    WHERE noun_id = :noun_id;
"""
