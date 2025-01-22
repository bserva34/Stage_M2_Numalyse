import easyocr

reader = easyocr.Reader(['fr', 'en'])  # Détecte le français et l'anglais
text = reader.readtext('test1.jpg', detail=0)
print(text)


text1 = reader.readtext('test2.jpg', detail=0)
print(text1)

text2 = reader.readtext('test3.jpg', detail=0)
print(text2)