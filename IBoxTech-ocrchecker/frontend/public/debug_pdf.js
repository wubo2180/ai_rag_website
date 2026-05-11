// 在浏览器控制台直接运行这段代码来调试PDF下载
async function debugPdfDownload(fileId = 1) {
    try {
        console.log('🔍 开始调试PDF下载, fileId:', fileId);
        
        // 获取token
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        console.log('🎫 Token状态:', token ? '存在' : '不存在');
        
        if (!token) {
            console.error('❌ 没有找到访问令牌');
            return;
        }
        
        // 1. 测试预签名URL
        console.log('📋 测试1: 预签名URL方式');
        try {
            const previewResponse = await fetch(`/api/files/${fileId}/preview`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            console.log('预签名URL响应状态:', previewResponse.status);
            const previewData = await previewResponse.json();
            console.log('预签名URL响应数据:', previewData);
            
        } catch (previewError) {
            console.warn('预签名URL测试失败:', previewError.message);
        }
        
        // 2. 测试直接下载
        console.log('📋 测试2: 直接下载方式');
        const downloadResponse = await fetch(`/api/files/${fileId}/download?preview=true`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('下载响应状态:', downloadResponse.status);
        console.log('下载响应头:', Object.fromEntries(downloadResponse.headers.entries()));
        
        if (!downloadResponse.ok) {
            const errorText = await downloadResponse.text();
            console.error('❌ 下载失败:', errorText);
            return;
        }
        
        const blob = await downloadResponse.blob();
        console.log('📦 下载的Blob信息:', {
            size: blob.size,
            type: blob.type
        });
        
        // 3. 验证PDF内容
        const arrayBuffer = await blob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        const header = String.fromCharCode(...uint8Array.slice(0, 4));
        console.log('📄 文件头验证:', {
            header: header,
            isValidPDF: header === '%PDF',
            first20Bytes: Array.from(uint8Array.slice(0, 20)).map(b => b.toString(16)).join(' ')
        });
        
        if (header !== '%PDF') {
            console.error('❌ 不是有效的PDF文件');
            const textContent = new TextDecoder().decode(uint8Array.slice(0, 500));
            console.error('文件内容预览:', textContent);
            return;
        }
        
        // 4. 测试PDF.js加载
        console.log('📋 测试3: PDF.js加载');
        const blobUrl = URL.createObjectURL(blob);
        console.log('🔗 Blob URL:', blobUrl);
        
        // 检查PDF.js是否可用
        if (typeof pdfjsLib === 'undefined') {
            console.error('❌ PDF.js未加载');
            return;
        }
        
        try {
            const pdf = await pdfjsLib.getDocument({
                url: blobUrl,
                cMapUrl: '//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
                cMapPacked: true
            }).promise;
            
            console.log('✅ PDF.js加载成功!', {
                numPages: pdf.numPages
            });
            
            // 清理
            URL.revokeObjectURL(blobUrl);
            
        } catch (pdfError) {
            console.error('❌ PDF.js加载失败:', pdfError);
            URL.revokeObjectURL(blobUrl);
        }
        
    } catch (error) {
        console.error('❌ 调试过程发生错误:', error);
    }
}

// 使用方法: debugPdfDownload(1)
console.log('📝 调试函数已加载，使用 debugPdfDownload(文件ID) 来测试');
