import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta    
import mysql.connector


# Page title
st.set_page_config(page_title='Support Ticket Workflow', page_icon='🎫', layout= 'wide')
st.title('🎫 Support Ticket Workflow')
st.info('To write a ticket, fill out the form below. Check status or review ticketing analytics using the tabs below.')

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="rahul",
        password="Rahul123@",
        database="tickets"
    )
    cursor = conn.cursor()

    # Run query
    cursor.execute("SELECT * FROM cust_ticket")
    results = cursor.fetchall()
    columns = [i[0] for i in cursor.description]

    # Create DataFrame
    df = pd.DataFrame(results, columns=columns)
    # Initialize session_state.df if not already set
    with st.expander("Data Preview"):
        st.dataframe(df)
    if 'df' not in st.session_state:
        st.session_state.df = df.copy()


    

except mysql.connector.Error as err:
    st.error(f"Database connection error: {err}")

def sort_df():
    st.session_state.df = edited_df.copy().sort_values(by = 'TicketID', ascending = False)

tabs = st.tabs(['Apply for Ticket','Ticket Status and Analytics'])
recent_ticket_number = int(max(st.session_state.df['TicketID']))

with tabs[0]:
    with st.form('addition'):
        name = st.text_input('Enter customer Name')
        product = st.text_input('Enter the product purchased')
        ticketType = st.selectbox('Type of issue',['Billing inquiry','Cancellation request','Product inquiry','Refund request','Technical issue'])
        ticketSubject = st.selectbox('Subject of issue',['Account access','Battery life','Cancellation request','Data loss','Delivery problem','Display issue',
                                                         'Hardware issue','Installation support','Network problem','Payment issue','Peripheral compatibility',
                                                         'Product compatibility','Product recommendation','Product setup','Refund request','Software bug'])
        description = st.text_area('Description of issue')
        priority = st.selectbox('Enter ticket priority',['Critical','High','Low','Medium'])
        channel = st.selectbox('Enter ticket channel',['Chat','Email','Phone','Social media'])
        submit = st.form_submit_button('Submit')
        
        if submit:
            today_date = datetime.now().strftime('%m/%d/%Y')
            df2 = pd.DataFrame([{'TicketID': recent_ticket_number + 1,
                             'CustomerName': name,
                             'ProductPurchased': product,
                             'TicketType': ticketType,
                             'TicketSubject': ticketSubject,
                             'TicketDescription': description,
                             'TicketStatus':'Open',
                             'Resolution': ' ',
                             'TicketPriority': priority,
                             'TicketChannel': channel,
                             'FirstResponseTime': today_date,
                             'TimetoResolution': '',
                             'CustomerSatisfactionRating': ''
                             }])
            st.write('Ticket submitted!')
            st.dataframe(df2, use_container_width=True, hide_index=True)
            st.session_state.df = pd.concat([st.session_state.df, df2], axis=0).sort_values(by='TicketID', ascending= False)

with tabs[1]:
    st.subheader('Support Ticket Status')
    st.session_state.df['TimetoResolution'] = pd.to_datetime(st.session_state.df['TimetoResolution'], errors='coerce')
    edited_df = st.data_editor(st.session_state.df,  use_container_width=True, hide_index= True, height = 210,
                               column_config= {
                                   'TicketStatus': st.column_config.SelectboxColumn(
                                       'TicketStatus',
                                        help = 'Ticket Status',
                                        options= ['Closed', 'Open', 'Pending Customer Response'],
                                        required= True,
                                   ),
                                    'TicketPriority': st.column_config.SelectboxColumn(
                                        'TicketPriority',
                                        help = 'Priority',
                                        options = ['Critical','High','Low','Medium'],
                                        required= True,
                                    ),
                                    'Resolution': st.column_config.TextColumn(
                                        'Resolution',
                                        help='Enter the resolution provided to the customer',
                                        required= False,
                                    ),
                                    'TimetoResolution': st.column_config.DateColumn(
                                        'TimetoResolution',
                                        help='Date the ticket is resolved',
                                        min_value=datetime(2000, 1, 1),  
                                        max_value=datetime.today(),  
                                        default=datetime.today(), 
                                        required=False
                                    ),
                                    'CustomerSatisfactionRating': st.column_config.SelectboxColumn(
                                        'CustomerSatisfactionRating',
                                        help = 'Enter the rating from 1 to 5',
                                        options= ['1','2','3','4','5'],
                                        required = False,
                                    ),
                               })

    st.subheader('Support Ticket Analytics')

    n_tickets_queue = len(st.session_state.df[st.session_state.df.TicketStatus=='Open'])
    n_tickets_pending = len(st.session_state.df[st.session_state.df.TicketStatus== 'Pending Customer Response'])
    steps = np.linspace(0, n_tickets_queue, num=30)

    st.session_state.df['TimetoResolution'] = pd.to_datetime(st.session_state.df['TimetoResolution'])
    st.session_state.df['FirstResponseTime'] = pd.to_datetime(st.session_state.df['FirstResponseTime'])

    st.session_state.df['Response Time (min)'] = (st.session_state.df['FirstResponseTime'] - st.session_state.df['TimetoResolution']).dt.total_seconds()/60
    average_response_time = st.session_state.df['Response Time (min)'].mean()
    
    col1,col2 = st.columns(2)

    with col1:
        st.metric(label="🎫 Tickets in Queue", value=n_tickets_queue)    
    

    with col2:
        st.metric(label="⏳ Pending Customer Response", value=n_tickets_pending)

    

    status_plot = alt.Chart(edited_df).mark_bar().encode(
        x= alt.X('month(FirstResponseTime):O', title='Ticket Incidence Month'),
        y = 'count():Q',
        xOffset= 'TicketStatus:N',
        color= 'TicketStatus:N'
    ).properties(title = 'Ticket status month-wise').configure_legend(orient= 'bottom',titleFontSize=14, labelFontSize=14, titlePadding=5)
    st.altair_chart(status_plot, use_container_width=True, theme='streamlit')

    
    col3,col4 = st.columns((2,2))

    with col3:
        priority_plot = px.pie(edited_df, names= 'TicketPriority', title= 'Current Ticket Priority')

        priority_plot.update_layout(
            legend = dict(orientation = "h", yanchor = 'bottom', y = -0.1, xanchor = 'center', x= 0.5, font = dict(size = 14)),
            title_font_size = 18
        )

        st.plotly_chart(priority_plot, use_container_width= True)

    with col4:
        channel_chart = px.pie(edited_df, names='TicketChannel', title='Tickets by Channel')
        
        channel_chart.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(size=14)),
            title_font_size=18
        )
        
        st.plotly_chart(channel_chart, use_container_width=True)

    col5,col6 = st.columns((2,2))

    with col5:
        ticket_counts = edited_df['TicketType'].value_counts().reset_index()
        ticket_counts.columns = ['TicketType', 'Count']
        
        ticket_type_chart = px.bar(ticket_counts, x='TicketType', y='Count', title='Ticket Count by Type', color='TicketType', text='Count')
        ticket_type_chart.update_traces(texttemplate='%{text}', textposition='inside')
        ticket_type_chart.update_layout(xaxis_title='Ticket Type', yaxis_title='Number of Tickets', showlegend=False, xaxis_tickangle=-45, title_font_size=18)
        
        st.plotly_chart(ticket_type_chart, use_container_width=True)
    
    with col6:
       subject_counts = edited_df['TicketSubject'].value_counts().reset_index()
       subject_counts.columns = ['TicketSubject', 'Count']
       ticket_subject_chart = px.pie(subject_counts, names='TicketSubject', values='Count', title='Tickets by Subject')
       
       ticket_subject_chart.update_layout(
           legend=dict(orientation='h', y=-0.2),
           title_font_size=18
        )
       
       st.plotly_chart(ticket_subject_chart, use_container_width=True)

if 'conn' in locals() and conn.is_connected():
    cursor.close()
    conn.close()