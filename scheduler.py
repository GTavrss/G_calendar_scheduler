import pandas as pd
from week import Week
from event import Event
from version0 import get_week
import numpy as np

#Coisas que faltam:
    # 1- Arrumar o re_schedule, para quando um evento passado for bloqueado, 
    #    remarcar somento os próximos incluindo esse.
    # 2- Histórico de eventos salvos em uma planilha
    # 3- Arrumar o sparce_scheduling para quando o dia estiver cheio <---- acho que já está feito
    # 4- Mais interabilidade com usuário.
    # 5- Force Scheduling
    # 6- Montar um dumb_schedule
    
    
class Scheduler():
    
    def __init__(self, relative_week=0):
        self.relative_week= relative_week
        self.week_start , self.week_end = get_week(self.relative_week)
        self.week = Week(self.week_start , self.week_end)
        
    def sparse_scheduling(self, event_list):
        for i in np.arange(0,len(event_list)):
            if event_list[i].daily:
                self.week.create_event(event_list[i])
            else:
                idx = np.mod(i,5)+1
                time = self.week.week_days[idx].next_time(event_list[i])
                self.week.create_event(event_list[i],time=time)
            
    def smart_schedule(self, root):
        T = pd.read_excel(root, sheet_name=0)
        T['Diário'] = T['Diário'].notna()
        T['Agendado'] = T['Agendado'].notna()
        T = T.sort_values(by=['Prioridade','Diário','Duração'])
        for p in T['Prioridade'].unique().tolist():
            T_= T.loc[T['Prioridade']==p]
            L = []
            for i in T_.index.tolist():
                E = Event(T.loc[i,'Nome'],T.loc[i,'Duração'],
                          T.loc[i,'Categoria'], priority = T.loc[i,'Prioridade'], 
                          scheduled=T.loc[i,'Agendado'], daily= T.loc[i,'Diário'])
                L.append(E)
            self.sparse_scheduling(L)
        
    def re_schedule(self, root):
        self.week.delete_all_created_events()
        self.smart_schedule(root)
        
        
    def delete_all_created_events(self):
        self.week.delete_all_created_events()
    
    
