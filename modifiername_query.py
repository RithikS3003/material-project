
GENERATE_MODIFIER_ID = """
    SELECT modifier_id
    FROM modifier_name_mstr
    ORDER BY modifier_id DESC
    LIMIT 1;
"""

GET_MODIFIER_VALUES = """
    SELECT modifier_id, modifier, isActive, abbreviation, description
    FROM modifier_name_mstr
    ORDER BY modifier_id;
"""

GET_MODIFIER_BY_ID = """
    SELECT modifier_id, modifier, isActive, abbreviation, description
    FROM modifier_name_mstr
    WHERE modifier_id = :modifier_id;
"""

CREATE_MODIFIER = """
    INSERT INTO modifier_name_mstr (modifier_id, modifier, abbreviation, description, isActive)
    VALUES (:modifier_id, :modifier, :abbreviation, :description, :isActive);
"""

UPDATE_MODIFIER = """
    UPDATE modifier_name_mstr
    SET modifier = :modifier, abbreviation = :abbreviation, description = :description, isActive = :isActive
    WHERE modifier_id = :modifier_id;
"""

DELETE_MODIFIER = """
    DELETE FROM modifier_name_mstr
    WHERE modifier_id = :modifier_id;
"""
