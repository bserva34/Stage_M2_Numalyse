class TimeManager():  # Hérite maintenant de QWidget
    def __init__(self):
        super().__init__()

    def m_to_mst(self,milliseconds):
        """ Formate un temps donné en millisecondes en mm:ss.d """
        total_seconds = milliseconds / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        tenths = int((total_seconds * 10) % 10)  # Extraction du dixième de seconde
        return f"{minutes:02}'{seconds:02}''{tenths}"

    def s_to_ms(self,seconds):
        """ Formate un temps donné en secondes en mm:ss. """
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"