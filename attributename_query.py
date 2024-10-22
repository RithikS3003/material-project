# queries.py

# SQL queries for attri_name_mstr table

GENERATE_MODIFIER_ID = "SELECT modifier_id FROM attri_name_mstr ORDER BY modifier_id DESC LIMIT 1;"

GET_MODIFIERS = """
    SELECT modifier_id, modifier, isActive, abbreviation, description
    FROM attri_name_mstr
    ORDER BY modifier_id;
"""

GET_MODIFIER_BY_ID = """
    SELECT modifier_id, modifier, isActive, abbreviation, description
    FROM attri_name_mstr
    WHERE modifier_id = :modifier_id;
"""

CREATE_MODIFIER = """
    INSERT INTO attri_name_mstr (modifier_id, modifier, abbreviation, description, isActive)
    VALUES (:modifier_id, :modifier, :abbreviation, :description, :isActive)
    RETURNING modifier_id, modifier, abbreviation, description, isActive;
"""

UPDATE_MODIFIER = """
    UPDATE attri_name_mstr
    SET modifier = :modifier,
        abbreviation = :abbreviation,
        description = :description,
        isActive = :isActive
    WHERE modifier_id = :modifier_id
    RETURNING modifier_id, modifier, abbreviation, description, isActive;
"""

DELETE_MODIFIER = """
    DELETE FROM attri_name_mstr
    WHERE modifier_id = :modifier_id;
"""
