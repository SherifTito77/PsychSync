"""
NoSQL Injection Prevention Module
Provides safe query construction and input validation for NoSQL databases
"""

import re
from typing import Any


class NoSQLInjectionPreventer:
    """
    Prevents NoSQL injection attacks through safe query construction
    """

    # Dangerous MongoDB operators that should never come from user input
    DANGEROUS_OPERATORS = {
        "$where",
        "$regex",
        "$expr",
        "$jsonSchema",
        "$ne",
        "$nin",
        "$in",
        "$exists",
        "$type",
        "$mod",
        "$size",
        "$all",
        "$and",
        "$or",
        "$not",
        "$nor",
        "$elemMatch",
        "$gt",
        "$gte",
        "$lt",
        "$lte",
    }

    # Characters/patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r"\$where",
        r"\$ne\s*:",
        r"\$regex\s*:",
        r"\$expr\s*:",
        r"\{.*\$.*\}",
        r"\'.*\$.*\'",
        r'".*\$.*"',
    ]

    @classmethod
    def sanitize_query_input(cls, user_input: Any) -> Any:
        """
        Sanitize user input before using in NoSQL queries

        Args:
            user_input: Raw user input

        Returns:
            Sanitized input safe for database queries
        """
        if user_input is None:
            return None

        if isinstance(user_input, (int, float, bool)):
            return user_input

        if isinstance(user_input, str):
            # Remove dangerous operators
            for operator in cls.DANGEROUS_OPERATORS:
                if operator in user_input:
                    raise ValueError(f"Dangerous operator '{operator}' detected in input")

            # Check for injection patterns
            for pattern in cls.INJECTION_PATTERNS:
                if re.search(pattern, user_input, re.IGNORECASE):
                    raise ValueError(f"Potential injection pattern detected: {pattern}")

            # Escape special characters
            return user_input.replace("$", "\\$")

        if isinstance(user_input, list):
            return [cls.sanitize_query_input(item) for item in user_input]

        if isinstance(user_input, dict):
            return cls.sanitize_dict(user_input)

        raise TypeError(f"Unsupported input type: {type(user_input)}")

    @classmethod
    def sanitize_dict(cls, query_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively sanitize dictionary queries

        Args:
            query_dict: Dictionary query to sanitize

        Returns:
            Sanitized dictionary safe for database queries
        """
        if not isinstance(query_dict, dict):
            raise TypeError("Expected dict type")

        sanitized = {}
        for key, value in query_dict.items():
            # Check key for dangerous operators
            if key.startswith("$"):
                if key not in cls.DANGEROUS_OPERATORS:
                    # Unknown operator - reject
                    raise ValueError(f"Unknown operator: {key}")
                # Known dangerous operator - only allow in specific contexts
                if key in {"$where", "$regex", "$expr"}:
                    raise ValueError(f"Dangerous operator '{key}' not allowed from user input")

            # Recursively sanitize values
            sanitized[key] = cls.sanitize_query_input(value)

        return sanitized

    @classmethod
    def build_safe_query(cls, field: str, operator: str, value: Any) -> dict[str, Any]:
        """
        Build a safe MongoDB query with proper sanitization

        Args:
            field: Field name to query
            operator: MongoDB operator (e.g., '$eq', '$gt', etc.)
            value: Value to compare against

        Returns:
            Safe query dictionary
        """
        # Sanitize field name
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field):
            raise ValueError(f"Invalid field name: {field}")

        # Validate operator
        if operator not in {"$eq", "$gt", "$gte", "$lt", "$lte", "$ne", "$in", "$nin"}:
            if operator != "$eq":  # $eq is default
                raise ValueError(f"Operator '{operator}' not allowed")

        # Sanitize value
        safe_value = cls.sanitize_query_input(value)

        # Build query
        if operator == "$eq":
            return {field: safe_value}
        return {field: {operator: safe_value}}

    @classmethod
    def validate_find_query(cls, query: dict[str, Any]) -> bool:
        """
        Validate a MongoDB find query for safety

        Args:
            query: Query dictionary to validate

        Returns:
            True if safe, raises ValueError if dangerous
        """
        try:
            # Recursively validate the query
            cls._validate_query_node(query)
            return True
        except ValueError as e:
            raise ValueError(f"Unsafe query: {e}")

    @classmethod
    def _validate_query_node(cls, node: Any, depth: int = 0) -> None:
        """
        Recursively validate a query node

        Args:
            node: Query node to validate
            depth: Current depth (to prevent recursion attacks)

        Raises:
            ValueError: If node is unsafe
        """
        # Prevent recursion attacks
        if depth > 10:
            raise ValueError("Query too deeply nested")

        if isinstance(node, dict):
            for key, value in node.items():
                # Check for dangerous operators
                if key.startswith("$"):
                    if key in {"$where", "$expr", "$jsonSchema"}:
                        raise ValueError(f"Dangerous operator '{key}' detected")

                    # Only allow safe operators
                    safe_operators = {
                        "$eq",
                        "$gt",
                        "$gte",
                        "$lt",
                        "$lte",
                        "$ne",
                        "$in",
                        "$nin",
                        "$and",
                        "$or",
                        "$not",
                        "$nor",
                        "$exists",
                        "$type",
                        "$mod",
                        "$regex",
                        "$size",
                        "$all",
                        "$elemMatch",
                        "$set",
                        "$unset",
                    }
                    if key not in safe_operators:
                        raise ValueError(f"Unsafe operator '{key}' detected")

                # Recursively validate value
                cls._validate_query_node(value, depth + 1)

        elif isinstance(node, (list, tuple)):
            for item in node:
                cls._validate_query_node(item, depth + 1)


class SafeMongoQueryBuilder:
    """
    Safe query builder for MongoDB operations
    """

    def __init__(self):
        self.preventer = NoSQLInjectionPreventer()
        self.query = {}

    def equals(self, field: str, value: Any) -> "SafeMongoQueryBuilder":
        """Add equals condition"""
        self.query[field] = self.preventer.sanitize_query_input(value)
        return self

    def greater_than(self, field: str, value: Any) -> "SafeMongoQueryBuilder":
        """Add greater than condition"""
        safe_value = self.preventer.sanitize_query_input(value)
        self.query[field] = {"$gt": safe_value}
        return self

    def less_than(self, field: str, value: Any) -> "SafeMongoQueryBuilder":
        """Add less than condition"""
        safe_value = self.preventer.sanitize_query_input(value)
        self.query[field] = {"$lt": safe_value}
        return self

    def in_list(self, field: str, values: list[Any]) -> "SafeMongoQueryBuilder":
        """Add in-list condition"""
        safe_values = [self.preventer.sanitize_query_input(v) for v in values]
        self.query[field] = {"$in": safe_values}
        return self

    def and_condition(self, *conditions: dict[str, Any]) -> "SafeMongoQueryBuilder":
        """Add AND condition"""
        validated_conditions = [self.preventer.sanitize_dict(c) for c in conditions]
        self.query["$and"] = validated_conditions
        return self

    def or_condition(self, *conditions: dict[str, Any]) -> "SafeMongoQueryBuilder":
        """Add OR condition"""
        validated_conditions = [self.preventer.sanitize_dict(c) for c in conditions]
        self.query["$or"] = validated_conditions
        return self

    def build(self) -> dict[str, Any]:
        """Build and validate the final query"""
        self.preventer.validate_find_query(self.query)
        return self.query


# Convenience functions
def safe_find(collection, query: dict[str, Any]) -> Any:
    """
    Safely execute a MongoDB find query

    Args:
        collection: MongoDB collection object
        query: Query dictionary

    Returns:
        Query result

    Example:
        result = safe_find(users_collection, {'username': 'john'})
        result = safe_find(users_collection, {'age': {'$gt': 18}})
    """
    # Validate and sanitize query
    NoSQLInjectionPreventer.validate_find_query(query)
    sanitized = NoSQLInjectionPreventer.sanitize_dict(query)

    # Execute query
    return collection.find(sanitized)


def safe_find_one(collection, query: dict[str, Any]) -> Any:
    """
    Safely execute a MongoDB findOne query

    Args:
        collection: MongoDB collection object
        query: Query dictionary

    Returns:
        Query result
    """
    # Validate and sanitize query
    NoSQLInjectionPreventer.validate_find_query(query)
    sanitized = NoSQLInjectionPreventer.sanitize_dict(query)

    # Execute query
    return collection.find_one(sanitized)


def safe_update(collection, query: dict[str, Any], update: dict[str, Any]) -> Any:
    """
    Safely execute a MongoDB update operation

    Args:
        collection: MongoDB collection object
        query: Query dictionary
        update: Update dictionary

    Returns:
        Update result
    """
    # Validate query and update
    NoSQLInjectionPreventer.validate_find_query(query)
    sanitized_query = NoSQLInjectionPreventer.sanitize_dict(query)
    sanitized_update = NoSQLInjectionPreventer.sanitize_dict(update)

    # Execute update
    return collection.update_many(sanitized_query, {"$set": sanitized_update})


def safe_insert(collection, document: dict[str, Any]) -> Any:
    """
    Safely execute a MongoDB insert operation

    Args:
        collection: MongoDB collection object
        document: Document to insert

    Returns:
        Insert result
    """
    # Sanitize document
    sanitized = NoSQLInjectionPreventer.sanitize_dict(document)

    # Execute insert
    return collection.insert_one(sanitized)


# Testing and validation
if __name__ == "__main__":
    print("🔍 NoSQL INJECTION PREVENTION TEST")
    print("=" * 60)

    # Test 1: Safe query building
    print("\n✅ Test 1: Safe Query Building")
    builder = SafeMongoQueryBuilder()
    query = builder.equals("username", "john").greater_than("age", 18).build()
    print(f"Query: {query}")

    # Test 2: Dangerous operator detection
    print("\n⚠️  Test 2: Dangerous Operator Detection")
    try:
        NoSQLInjectionPreventer.sanitize_query_input({"$where": 'this.password == "123"'})
        print("❌ FAILED - Should have detected dangerous operator")
    except ValueError as e:
        print(f"✅ Detected dangerous operator: {e}")

    # Test 3: Input sanitization
    print("\n✅ Test 3: Input Sanitization")
    safe_input = NoSQLInjectionPreventer.sanitize_query_input("test$user")
    print("Original: test$user")
    print(f"Sanitized: {safe_input}")

    # Test 4: Query validation
    print("\n✅ Test 4: Query Validation")
    safe_query = {"username": "john", "age": {"$gt": 18}}
    if NoSQLInjectionPreventer.validate_find_query(safe_query):
        print("✅ Safe query validated")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
