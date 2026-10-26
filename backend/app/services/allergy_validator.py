"""
FoodVerse AI — Deterministic Allergy & Dietary Safety Barrier.

This service executes AFTER model generation and BEFORE response serialization.
It enforces a zero-trust policy: the LLM is never trusted blindly with allergy safety.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

# Comprehensive taxonomy of common food allergens and their ingredient synonyms
ALLERGEN_SYNONYMS: Dict[str, Set[str]] = {
    "peanut": {
        "peanut", "peanuts", "peanut butter", "peanut oil", "arachis", "groundnut", "groundnuts", "beer nuts"
    },
    "tree_nut": {
        "almond", "almonds", "walnut", "walnuts", "cashew", "cashews", "pecan", "pecans",
        "pistachio", "pistachios", "macadamia", "hazelnut", "hazelnuts", "praline", "marzipan", "pesto"
    },
    "dairy": {
        "milk", "dairy", "butter", "cheese", "cream", "yogurt", "yoghurt", "whey", "casein",
        "ghee", "lactose", "curd", "paneer", "parmesan", "mozzarella", "cheddar", "brie", "ricotta"
    },
    "egg": {
        "egg", "eggs", "yolk", "albumin", "egg white", "mayonnaise", "mayo", "poached egg",
        "scrambled egg", "omelette", "meringue", "custard"
    },
    "gluten": {
        "wheat", "gluten", "flour", "bread", "pasta", "rye", "barley", "semolina", "spelt",
        "couscous", "toast", "cracker", "soy sauce"
    },
    "shellfish": {
        "shrimp", "shrimps", "prawn", "prawns", "crab", "lobster", "crawfish", "scallop",
        "scallops", "oyster", "oysters", "clam", "clams", "mussel", "mussels", "squid", "calamari", "octopus"
    },
    "soy": {
        "soy", "soya", "soybean", "soybeans", "tofu", "edamame", "soy sauce", "tamari", "tempeh", "miso"
    },
    "fish": {
        "fish", "salmon", "tuna", "cod", "tilapia", "halibut", "trout", "anchovy", "anchovies",
        "sardine", "sardines", "mackerel", "bass", "snapper"
    },
    "sesame": {
        "sesame", "sesame seeds", "sesame oil", "tahini", "hummus"
    },
    "vegetarian": {
        "chicken", "beef", "pork", "meat", "bacon", "turkey", "duck", "lamb", "fish", "salmon",
        "tuna", "shrimp", "seafood", "gelatin", "lard", "veal", "ham"
    },
    "vegan": {
        "chicken", "beef", "pork", "meat", "bacon", "turkey", "duck", "lamb", "fish", "salmon",
        "tuna", "shrimp", "seafood", "gelatin", "lard", "veal", "ham", "milk", "cheese", "butter",
        "cream", "yogurt", "egg", "eggs", "honey", "whey", "casein", "ghee"
    },
}



class AllergyValidator:
    """Deterministic barrier scanning ingredients against declared user allergies."""

    def normalize_declared_allergens(self, raw_input: str) -> List[str]:
        """Convert comma/space separated input into normalized canonical allergen keys."""
        if not raw_input or not raw_input.strip():
            return []
        
        # Split by commas, semicolons, or 'and'
        tokens = re.split(r"[,;]|\band\b", raw_input.lower())
        declared = []
        for token in tokens:
            cleaned = token.strip()
            # Remove filler words like 'e.g.', 'allergic to', 'none'
            cleaned = re.sub(r"^(e\.g\.|allergic to|allergy to|no|none)\s*", "", cleaned).strip()
            if cleaned and cleaned not in {"none", "n/a", "no allergies", "nil"}:
                declared.append(cleaned)
        return declared

    def validate_meal_ingredients(
        self,
        meal_name: str,
        ingredients: List[str],
        declared_allergens: List[str],
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate ingredients of a meal against declared allergies.

        Returns:
            Tuple of (is_safe, list_of_violating_ingredients, list_of_detected_allergens)
        """
        if not declared_allergens:
            return True, [], []

        violations: List[str] = []
        detected_allergens: Set[str] = set()

        for allergen in declared_allergens:
            allergen_clean = allergen.lower().strip()
            # Match against known synonym sets
            synonym_set = set()
            for key, synonyms in ALLERGEN_SYNONYMS.items():
                if allergen_clean in key or any(allergen_clean in s for s in synonyms):
                    synonym_set.update(synonyms)
            # Add the literal allergen itself
            synonym_set.add(allergen_clean)

            # Check meal title
            meal_lower = meal_name.lower()
            for syn in synonym_set:
                if self._token_matches(syn, meal_lower):
                    violations.append(f"{meal_name} (in title: '{syn}')")
                    detected_allergens.add(allergen_clean)
                    break

            # Check each ingredient
            for ing in ingredients:
                ing_lower = ing.lower()
                for syn in synonym_set:
                    if self._token_matches(syn, ing_lower):
                        violations.append(f"'{ing}' (contains '{syn}')")
                        detected_allergens.add(allergen_clean)
                        break

        is_safe = len(violations) == 0
        return is_safe, list(set(violations)), list(detected_allergens)

    def _token_matches(self, pattern: str, text: str) -> bool:
        """Word-boundary regex match to prevent false substrings (e.g. 'egg' in 'eggplant')."""
        if pattern == "egg":
            # Explicitly exclude eggplant
            if "eggplant" in text:
                text = text.replace("eggplant", "")
        # Match whole word or phrase
        regex = r"(^|\b|\W)" + re.escape(pattern) + r"($|\b|\W)"
        return bool(re.search(regex, text))


# Global singleton instance
allergy_validator = AllergyValidator()
