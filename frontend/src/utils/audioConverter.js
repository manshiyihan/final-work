/**
 * 音频格式转换工具
 * 将录音转换为16kHz单声道WAV格式
 */

export async function convertAudioTo16kMono(audioBlob) {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const fileReader = new FileReader()

    fileReader.onload = async (e) => {
      try {
        const arrayBuffer = e.target.result
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
        
        // 重采样到16kHz
        const targetSampleRate = 16000
        const offlineContext = new OfflineAudioContext(
          1, // 单声道
          audioBuffer.duration * targetSampleRate,
          targetSampleRate
        )

        const source = offlineContext.createBufferSource()
        source.buffer = audioBuffer
        source.connect(offlineContext.destination)
        source.start()

        const renderedBuffer = await offlineContext.startRendering()
        
        // 转换为WAV格式
        const wavBlob = bufferToWave(renderedBuffer, targetSampleRate)
        resolve(wavBlob)
      } catch (error) {
        reject(error)
      }
    }

    fileReader.onerror = reject
    fileReader.readAsArrayBuffer(audioBlob)
  })
}

/**
 * 将AudioBuffer转换为WAV格式的Blob
 */
function bufferToWave(audioBuffer, sampleRate) {
  const numberOfChannels = audioBuffer.numberOfChannels
  const length = audioBuffer.length * numberOfChannels * 2
  const buffer = new ArrayBuffer(44 + length)
  const view = new DataView(buffer)
  const channels = []
  let offset = 0
  let pos = 0

  // 写入WAV文件头
  setUint32(0x46464952) // "RIFF"
  setUint32(36 + length) // file length - 8
  setUint32(0x45564157) // "WAVE"
  setUint32(0x20746d66) // "fmt " chunk
  setUint32(16) // length = 16
  setUint16(1) // PCM (uncompressed)
  setUint16(numberOfChannels)
  setUint32(sampleRate)
  setUint32(sampleRate * 2 * numberOfChannels) // avg. bytes/sec
  setUint16(numberOfChannels * 2) // block-align
  setUint16(16) // 16-bit
  setUint32(0x61746164) // "data" - chunk
  setUint32(length) // chunk length

  // 写入音频数据
  for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
    channels.push(audioBuffer.getChannelData(i))
  }

  while (pos < audioBuffer.length) {
    for (let i = 0; i < numberOfChannels; i++) {
      let sample = Math.max(-1, Math.min(1, channels[i][pos]))
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      view.setInt16(44 + offset, sample, true)
      offset += 2
    }
    pos++
  }

  return new Blob([buffer], { type: 'audio/wav' })

  function setUint16(data) {
    view.setUint16(pos, data, true)
    pos += 2
  }

  function setUint32(data) {
    view.setUint32(pos, data, true)
    pos += 4
  }
}
