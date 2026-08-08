        
                    )
                continue

            text += format_bookmaker(
                bookmaker_name,
                markets
            )

            text += "\n"

        # Пока просто показываем реальные данные.
        # Прогнозы подключим после проверки.
        if len(text) > 3800:
            await send_message(text[:3800])
        else:
            await se
