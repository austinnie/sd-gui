# core/pipeline/steps/remove_clothes_step.py
"""去掉衣服 - 将人物转换为裸体风格 - 支持 ControlNet"""

import os
import torch
from PIL import Image
from datetime import datetime
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

from ..step import PipelineStep, StepContext, StepResult, StepStatus
from .controlnet_mixin import ControlNetMixin


class RemoveClothesStep(PipelineStep, ControlNetMixin):
    """去掉衣服转换步骤 - 支持 ControlNet"""
    
    def __init__(self):
        super().__init__("remove_clothes", "去掉衣服 - 转换为裸体")
        self._config = {
            "strength": 0.55,
            "cfg": 7.0,
            "steps": 35,
            "model_path": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
            "use_controlnet": False,
            "controlnet_type": "openpose",
            "controlnet_strength": 0.7,
        }
    
    def get_config_schema(self):
        return {
            "strength": {"type": "float", "default": 0.55, "min": 0.35, "max": 0.75},
            "cfg": {"type": "float", "default": 7.0, "min": 5, "max": 10},
            "steps": {"type": "int", "default": 35, "min": 25, "max": 60},
            "model_path": {"type": "str", "default": "../models/sd-v1-5/aiiiiii01_v10.safetensors"},
            "use_controlnet": {"type": "bool", "default": False},
            "controlnet_type": {"type": "str", "default": "openpose", 
                               "choices": ["openpose", "canny", "hed", "lineart"]},
            "controlnet_strength": {"type": "float", "default": 0.7, "min": 0.3, "max": 1.0},
        }
    

    def _generate_remove_clothes_prompts(self) -> list:
        """生成素描风格提示词 - 扩展版 8种场景"""
        return [    
        {
            "name": "比基尼→裸体_海滩",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, standing on tropical beach, ocean waves, golden sunset, full body, perfect body, natural beauty, sun-kissed skin, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "比基尼→裸体_泳池",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, sitting by swimming pool, water reflections, summer atmosphere, full body, perfect body, natural beauty, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "比基尼→裸体_游艇",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, on a luxury yacht, ocean background, golden lighting, full body, perfect body, glamorous, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "比基尼→裸体_温泉",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in hot spring, steam rising, natural rock background, relaxing atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, bikini, swimsuit, bathing suit, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 紧身衣/瑜伽服 → 裸体 (强度: 0.50-0.60) =====
        {
            "name": "瑜伽服→裸体_瑜伽",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, doing yoga pose, flexible body, yoga mat, peaceful atmosphere, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, yoga pants, leggings, sports bra, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "紧身衣→裸体_健身房",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in gym, fit body, defined muscles, workout atmosphere, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sports bra, leggings, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "紧身衣→裸体_跑步",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, running, dynamic pose, fit body, outdoor setting, full body, perfect body, natural lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sports bra, leggings, running clothes, gym clothes, fitness wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 正装/外套 → 裸体 (强度: 0.55-0.65) =====
        {
            "name": "西装→裸体_办公室",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in modern office, professional setting, confident pose, full body, perfect body, dramatic lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, suit, blazer, jacket, tie, dress shirt, business wear, formal wear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "风衣→裸体_街头",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, urban street background, city atmosphere, confident pose, full body, perfect body, dramatic lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, trench coat, jacket, outerwear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "大衣→裸体_雪地",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in snowy landscape, winter atmosphere, contrast of warm skin and cold snow, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, coat, parka, winter jacket, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "礼服→裸体_红毯",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, glamorous red carpet setting, dramatic lighting, elegant pose, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, evening gown, formal dress, red carpet dress, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 宽松衣物 → 裸体 (强度: 0.60-0.70) =====
        {
            "name": "连衣裙→裸体_花园",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in flower garden, natural beauty, surrounded by flowers, full body, perfect body, soft lighting, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, dress, sundress, floral dress, clothes, fabric, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "T恤→裸体_家居",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, cozy home atmosphere, morning sunlight, natural beauty, relaxed pose, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, t-shirt, hoodie, sweatpants, casual clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "睡衣→裸体_卧室",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in bedroom, soft morning light, cozy sheets, natural beauty, intimate atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, pajamas, nightgown, sleepwear, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "毛衣→裸体_沙发",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, on cozy sofa, warm lighting, comfortable atmosphere, natural beauty, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sweater, knitwear, warm clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 职业装 → 裸体 (强度: 0.55-0.65) =====
        {
            "name": "护士服→裸体_病房",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in hospital setting, medical atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, nurse uniform, scrubs, medical clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar, gore, blood"
        },
        {
            "name": "女仆装→裸体_豪宅",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in luxurious mansion, elegant setting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, maid outfit, apron, uniform, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "空姐装→裸体_机舱",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in airplane cabin, dramatic lighting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, flight attendant uniform, airline uniform, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "警察制服→裸体_城市",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, urban night setting, dramatic lighting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, police uniform, patrol uniform, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 校服/学生装 → 裸体 (强度: 0.50-0.60) =====
        {
            "name": "校服→裸体_教室",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful young woman, nude, naked, bare skin, in classroom, school setting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, school uniform, student clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar, underage"
        },
        {
            "name": "体育服→裸体_操场",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful young woman, nude, naked, bare skin, on sports field, outdoor setting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, gym uniform, sports uniform, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 特殊服装 → 裸体 (强度: 0.55-0.65) =====
        {
            "name": "和服→裸体_庭院",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in traditional Japanese garden, cherry blossoms, serene atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, kimono, yukata, traditional clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "汉服→裸体_古风",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in traditional Chinese garden, ancient atmosphere, elegant setting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, hanfu, traditional Chinese clothes, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "婚纱→裸体_教堂",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in cathedral, dramatic lighting, romantic atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, wedding dress, bridal gown, lace dress, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "紧身裙→裸体_派对",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, at glamorous party, nightclub atmosphere, dramatic lighting, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, cocktail dress, party dress, mini dress, clothes, fabric, dress, shirt, pants, underwear, bra, panties, covering, clothed, explicit, pornographic, vulgar"
        },
        
        # ===== 内衣/情趣内衣 → 裸体 (强度: 0.40-0.50) =====
        {
            "name": "蕾丝内衣→裸体_卧室",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, in bedroom, soft romantic lighting, intimate atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, lace, lingerie, underwear, bra, panties, clothes, fabric, dress, shirt, pants, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "丁字裤→裸体_床边",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, sitting on bed, morning light, natural beauty, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, thong, underwear, panties, clothes, fabric, dress, shirt, pants, covering, clothed, explicit, pornographic, vulgar"
        },
        {
            "name": "情趣内衣→裸体_暗光",
            "prompt": "masterpiece, best quality, photorealistic, 8k, a beautiful woman, nude, naked, bare skin, dramatic shadows, intimate atmosphere, full body, perfect body, artistic nude, high quality, detailed face",
            "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature, sheer, lace, lingerie, underwear, bra, panties, clothes, fabric, dress, shirt, pants, covering, clothed, explicit, pornographic, vulgar"
        }
    ]
			
    def execute(self, context: StepContext) -> StepResult:
        """执行去掉衣服转换 - 支持 ControlNet"""
        config = self._config
        image_path = context.input_path
        
        if not os.path.exists(image_path):
            return StepResult(
                status=StepStatus.FAILED,
                error=f"图片不存在: {image_path}"
            )
        
        output_dir = os.path.join(context.output_dir, "remove_clothes")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            pipe = context.global_config.get('pipe')
            model_path = context.global_config.get('model_path')
            
            init_image = Image.open(image_path).convert('RGB')
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # ===== 设置 ControlNet =====
            controlnet_pipe, control_image, use_controlnet = self._setup_controlnet(
                config, model_path, image_path, init_image
            )
            
            if controlnet_pipe is not None:
                pipe = controlnet_pipe
            
            if pipe is None and model_path:
                common_args = {
                    "torch_dtype": torch.float32,
                    "safety_checker": None,
                    "requires_safety_checker": False,
                    "use_safetensors": True,
                    "low_cpu_mem_usage": True,
                }
                pipe = StableDiffusionPipeline.from_single_file(model_path, **common_args)
                pipe.to("cpu")
                pipe.enable_vae_slicing()
                pipe.enable_attention_slicing()
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            
            if pipe is None:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="无法获取 Pipeline"
                )
            
            # ===== 场景数限制 =====
            max_scenes = self._get_scene_limit(config)
            all_prompts = self._generate_remove_clothes_prompts()
            if max_scenes is not None and max_scenes > 0:
                prompts = self._limit_prompts(all_prompts, max_scenes)
                print(f"   📊 场景限制: 只生成前 {len(prompts)}/{len(all_prompts)} 个场景")
            else:
                prompts = all_prompts
    
            strength = config.get("strength", 0.55)
            steps = config.get("steps", 35)
            cfg = config.get("cfg", 7.0)
            
            generator = torch.Generator("cpu").manual_seed(42)
            success_count = 0
            
            for idx, job in enumerate(prompts):
                # ✅ 检查取消
                if context.is_cancelled():
                    print(f"   ⏹️ 用户取消，已生成 {idx}/{7} 张")
                    return StepResult(
                        status=StepStatus.FAILED,
                        error="用户取消",
                        output_path=output_dir,
                        metadata={
                            "output_count": idx,
                            "output_dir": output_dir,
                            "success_count": success_count,
                            "cancelled": True,
                        }
                    )
                print(f"   [{idx+1}/{len(prompts)}] {job.get('name', 'unknown')}")
                
                gen_kwargs = {
                    "prompt": job.get("prompt", ""),
                    "negative_prompt": job.get("negative", ""),
                    "image": init_image,
                    "strength": strength,
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "generator": generator,
                }
                
                if control_image is not None and controlnet_pipe is not None:
                    gen_kwargs["control_image"] = control_image
                    gen_kwargs["controlnet_conditioning_scale"] = config.get("controlnet_strength", 0.7)
                    if idx == 0:
                        print(f"      🎛️ ControlNet 强度: {config.get('controlnet_strength', 0.7)}")
                
                result = pipe(**gen_kwargs)
                
                output_path = os.path.join(output_dir, f"{idx+1:02d}_{job.get('name', 'remove_clothes')}.png")
                result.images[0].save(output_path)
                success_count += 1
                print(f"      ✅ 已保存: {os.path.basename(output_path)}")
            
            return StepResult(
                status=StepStatus.SUCCESS if success_count > 0 else StepStatus.FAILED,
                output_path=output_dir,
                metadata={
                    "output_count": len(prompts),
                    "output_dir": output_dir,
                    "success_count": success_count,
                    "controlnet_used": control_image is not None,
                }
            )
                    
        except Exception as e:
            error_msg = str(e)
            if "取消" in error_msg or "cancelled" in error_msg.lower():
                print(f"      ⏹️ 生成被取消")
                return StepResult(
                    status=StepStatus.FAILED,
                    error="用户取消",
                    output_path=output_dir,
                    metadata={
                        "output_count": idx,
                        "output_dir": output_dir,
                        "success_count": success_count,
                        "cancelled": True,
                    }
                )
            print(f"      ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            # continue (已移除，不在循环中)