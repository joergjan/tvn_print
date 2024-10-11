from escpos.printer import Network

kitchen = Network("192.168.1.148")  # Printer IP Address
kitchen.text("Hello Benno\n")
kitchen.barcode('4006381333931', 'EAN13', 64, 2, '', '')
kitchen.cut()
