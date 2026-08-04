    # =======================================================================
    # SECURITY 1: IP-based rate limiting
    # =======================================================================
    redis_client = await redis.asyncio.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

    try:
        registration_key = f"registrations:{client_ip}"

        # Check registration count for this IP
        attempts = await redis_client.incr(registration_key)

        if attempts == 1:
            # Set expiry on first attempt (1 hour)
            await redis_client.expire(registration_key, 3600)

        if attempts > 3:  # Max 3 registrations per hour per IP
            await redis_client.close()
            logger.warning(f"Rate limit exceeded for registration from IP: {client_ip}")
            raise HTTPException(
