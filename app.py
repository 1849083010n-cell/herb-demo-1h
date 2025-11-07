import pandas as pd
import streamlit as st

# 读取分类结果文件
try:
    data = pd.read_csv('classification_results.csv')
except FileNotFoundError:
    st.error("未找到分类结果文件 'classification_results.csv'，请确保文件在正确路径下。")
    st.stop()

# 按心肝脾肺肾分类
heart_data = data[data['主要对应脏腑'] == '心']
liver_data = data[data['主要对应脏腑'] == '肝']
spleen_data = data[data['主要对应脏腑'] == '脾']
lung_data = data[data['主要对应脏腑'] == '肺']
kidney_data = data[data['主要对应脏腑'] == '肾']

# 设置页面标题
st.title('中药材按心肝脾肺肾分类展示')

# 展示心类中药材
st.header('心类中药材')
if not heart_data.empty:
    st.dataframe(heart_data[['药材名称', '功效']])
else:
    st.info('暂无心类中药材数据')

# 展示肝类中药材
st.header('肝类中药材')
if not liver_data.empty:
    st.dataframe(liver_data[['药材名称', '功效']])
else:
    st.info('暂无肝类中药材数据')

# 展示脾类中药材
st.header('脾类中药材')
if not spleen_data.empty:
    st.dataframe(spleen_data[['药材名称', '功效']])
else:
    st.info('暂无脾类中药材数据')

# 展示肺类中药材
st.header('肺类中药材')
if not lung_data.empty:
    st.dataframe(lung_data[['药材名称', '功效']])
else:
    st.info('暂无肺类中药材数据')

# 展示肾类中药材
st.header('肾类中药材')
if not kidney_data.empty:
    st.dataframe(kidney_data[['药材名称', '功效']])
else:
    st.info('暂无肾类中药材数据')
