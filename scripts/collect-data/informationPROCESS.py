#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 15:11:27 2019

@author: ermesonandrade
"""

#https://psutil.readthedocs.io/en/latest/

#https://www.thepythoncode.com/article/get-hardware-system-information-python

import os
import time
import datetime
import argparse

#-----------------------------------------------------------------------

def coletaProcesssos (name):
    
    #Obtem os processos através do ps. 
    output = os.popen('ps -eo user,pid,vsz,rss,%mem,command --sort=%mem | sed "s#^#$(date +%d/%m/%Y+%H:%M:%S) #"').read()
    print(output)
    
    #Abre o arquivo
    with open(name,'a+') as file:
        #Escreve no arquivo
        file.write(output)
        file.flush()
        
    #Fecha o arquivo.
    file.close()


#Parser usado para facilitar a criação de arquivos
parser = argparse.ArgumentParser(description = 'Entradas')
parser.add_argument('--dispositivo', action = 'store', dest = 'd',
                           required = True, help = 'Cloud or Edge.')
parser.add_argument('--workload', action = 'store', dest = 'w', required = True,
                           help = '0.1, 0.5 or 1.0')
arguments = parser.parse_args()
name = "processes" + arguments.d + "_" + arguments.w + ".txt"

while True:
    
    #chama a função que coleta os processos.
    coletaProcesssos(name)
    
    #Espera 60 segundos para coletar novamente.
    time.sleep(60) 
    
