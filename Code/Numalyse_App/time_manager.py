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

    def m_to_hms(self, milliseconds):
        """ Formate un temps donné en millisecondes en hh:mm:ss.d """
        total_seconds = milliseconds / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def m_to_hmsf(self, milliseconds):
        """ Formate un temps donné en millisecondes en hh:mm:ss:ff """
        total_seconds = milliseconds / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        # Calcul des frames : le reste des millisecondes divisé par 40 (pour 25 fps)
        frame = int((milliseconds % 1000) // 40)
        return f"{hours:02}:{minutes:02}:{seconds:02}[{frame:02}]"
