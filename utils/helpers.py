def parse_time_input(time_input: str) -> list:
    """Analisa a entrada de horários do usuário e retorna uma lista formatada"""
    try:
        times = [t.strip() for t in time_input.split(",")]
        valid_times = []
        
        for t in times:
            if len(t.split(":")) == 2:
                hours, minutes = map(int, t.split(":"))
                if 0 <= hours < 24 and 0 <= minutes < 60:
                    valid_times.append(f"{hours:02d}:{minutes:02d}")
        
        return valid_times if valid_times else None
    except:
        return None