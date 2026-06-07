/*
 Navicat Premium Dump SQL

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80044 (8.0.44)
 Source Host           : localhost:3306
 Source Schema         : gravity_matrix

 Target Server Type    : MySQL
 Target Server Version : 80044 (8.0.44)
 File Encoding         : 65001

 Date: 07/06/2026 14:41:07
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for app_settings
-- ----------------------------
DROP TABLE IF EXISTS `app_settings`;
CREATE TABLE `app_settings`  (
  `key` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`key`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_settings
-- ----------------------------
INSERT INTO `app_settings` VALUES ('default_template_id', 'tv-drama', '2026-06-07 14:38:35');

-- ----------------------------
-- Table structure for chapters
-- ----------------------------
DROP TABLE IF EXISTS `chapters`;
CREATE TABLE `chapters`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `number` int NOT NULL,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `project_id`(`project_id` ASC) USING BTREE,
  INDEX `ix_chapters_id`(`id` ASC) USING BTREE,
  CONSTRAINT `chapters_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 24 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chapters
-- ----------------------------
INSERT INTO `chapters` VALUES (9, 2, 1, '初入城市', '林默背着吉他，站在城市最大的地铁站出口。手机屏幕上的租房信息翻了又翻，电池只剩下百分之三。他把最后一格电留给了梦想，提着行李箱走进了陌生的人潮。');
INSERT INTO `chapters` VALUES (10, 2, 2, '温暖相遇', '车站广场上，一个短发的女孩提着一袋日用品经过，看见林默在翻地图。\"你看起来需要帮忙。\"她自然地开口。她的名字叫苏晴，从此两人开始了同一屋檐下的合租生活。');
INSERT INTO `chapters` VALUES (11, 2, 3, '现实门槛', '音乐公司面试间的冷白灯光让林默不太自在。他弹完了自己最拿手的曲子后，制作人周亦辰合上简历：\"你的技巧确实不错，但我听不到你自己的声音。\"');
INSERT INTO `chapters` VALUES (12, 2, 4, '友情考验', '苏晴偷偷把林默的 demo 发给了小剧场导演。两人发生了一场至今最激烈的争吵。当晚，苏晴留下一张纸条：\"我只是想让你的声音被人听见。\"');
INSERT INTO `chapters` VALUES (13, 2, 5, '破茧成蝶', '小剧场的后台灯光昏暗。林默握紧吉他，想起周亦辰的话，想起苏晴的纸条。幕布拉开，他不再紧张，弹出了一首只属于自己的歌。');
INSERT INTO `chapters` VALUES (14, 3, 1, '烽火狼烟', '北疆边塞，烽火台狼烟升腾。年轻的将军顾晏策马登上城墙，望着远处黑压压的敌军阵列。\"传令下去，今夜固守，不得擅自出战。\"');
INSERT INTO `chapters` VALUES (15, 3, 2, '帐中谋', '军帐内烛光摇曳。一位面色清秀的年轻士兵站在舆图前：\"将军，敌军看似强大，实则粮道空虚。\"这个新兵名叫江晚，眼神里有不属于普通士兵的锐利。');
INSERT INTO `chapters` VALUES (16, 3, 3, '暗流涌动', '京城来的密使带来了新的圣旨。顾晏捏着那一纸命令沉默了很久。\"将在外，君命有所不受。\"江晚在身后轻声说了一句。');
INSERT INTO `chapters` VALUES (17, 4, 1, '风暴', '远洋科考船\"极光号\"在十二级风暴里挣扎。船舱里，海洋生物学家陈深握紧扶手，透过模糊的舷窗，隐约看见一个巨大的黑影从船底游过。');
INSERT INTO `chapters` VALUES (18, 4, 2, '深海信号', '\"极光号\"漂在风暴之后的平静海面上。船底声呐记录了一段异常低频信号——那声音不像任何已知生物。陈深反复播放录音：\"它在回应我们的脉冲。\"');
INSERT INTO `chapters` VALUES (19, 4, 3, '下潜', '深潜器缓缓降入蔚蓝。数百米深处突然亮起蓝色光点，组成规则的几何图案。方晓抓住了陈深的胳膊：\"那是...一座城市。\"');
INSERT INTO `chapters` VALUES (20, 5, 1, '第一章', '这是废弃的旧稿内容，已被删除到回收站。');
INSERT INTO `chapters` VALUES (21, 6, 1, '阴差阳错', '夏浅浅只是去取一份文件，却在民政局门口被一辆黑色轿车溅了身水。车门打开，一个男人西装革履地看着她，开口第一句不是道歉：\"你在等人？正好，我需要一个临时的新娘。\"');
INSERT INTO `chapters` VALUES (22, 6, 2, '隐藏身份', '\"我只是个合同上的名字。\"夏浅浅对着闺蜜的消息苦笑。转身望着窗外城市的天际线，陆氏集团总裁的身影在落地玻璃上被夕阳拉得很长。');
INSERT INTO `chapters` VALUES (23, 6, 3, '终极考验', '家族敌人设下的商业陷阱即将吞噬整个集团。陆辰将签字笔放在夏浅浅面前：\"只有你能签——以陆太太的身份。\"这不是交易，是一份比合同更重的信任。');

-- ----------------------------
-- Table structure for jobs
-- ----------------------------
DROP TABLE IF EXISTS `jobs`;
CREATE TABLE `jobs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `progress` int NOT NULL,
  `current_step` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `result_id` int NULL DEFAULT NULL,
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `project_id`(`project_id` ASC) USING BTREE,
  INDEX `ix_jobs_id`(`id` ASC) USING BTREE,
  CONSTRAINT `jobs_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of jobs
-- ----------------------------
INSERT INTO `jobs` VALUES (3, 2, 'analysis', 'succeeded', 100, '分析完成', NULL, NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `jobs` VALUES (4, 2, 'script_generation', 'succeeded', 100, '生成完成', NULL, NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `jobs` VALUES (5, 3, 'analysis', 'succeeded', 100, '分析完成', NULL, NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `jobs` VALUES (6, 6, 'analysis', 'succeeded', 100, '分析完成', NULL, NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `jobs` VALUES (7, 6, 'script_generation', 'succeeded', 100, '生成完成', NULL, NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');

-- ----------------------------
-- Table structure for project_generation_settings
-- ----------------------------
DROP TABLE IF EXISTS `project_generation_settings`;
CREATE TABLE `project_generation_settings`  (
  `project_id` int NOT NULL,
  `settings_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`project_id`) USING BTREE,
  CONSTRAINT `project_generation_settings_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_generation_settings
-- ----------------------------

-- ----------------------------
-- Table structure for projects
-- ----------------------------
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `author` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `analysis_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `script_yaml` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `generation_settings_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `deleted_at` datetime NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_projects_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of projects
-- ----------------------------
INSERT INTO `projects` VALUES (2, '星辰之下', '林默', 'script_edited', '{\"characters\": [{\"id\": \"char_001\", \"name\": \"林默\", \"role\": \"主角\", \"gender\": \"男\", \"age\": 24, \"description\": \"怀揣音乐梦想来到大城市的年轻人\"}, {\"id\": \"char_002\", \"name\": \"苏晴\", \"role\": \"室友\", \"gender\": \"女\", \"age\": 25, \"description\": \"行动力强、性格温暖的合租室友\"}, {\"id\": \"char_003\", \"name\": \"周亦辰\", \"role\": \"制作人\", \"gender\": \"男\", \"age\": 32, \"description\": \"克制冷静的音乐制作人，代表行业门槛\"}], \"locations\": [{\"id\": \"loc_001\", \"name\": \"地铁站\", \"description\": \"城市交通枢纽，人来人往\"}, {\"id\": \"loc_002\", \"name\": \"合租出租屋\", \"description\": \"小但温馨的房间\"}, {\"id\": \"loc_003\", \"name\": \"音乐公司面试间\", \"description\": \"冷白灯光，专业但不近人情\"}], \"chapter_summaries\": [{\"chapter_number\": 1, \"title\": \"初入城市\", \"summary\": \"林默带着吉他来到陌生城市\"}, {\"chapter_number\": 2, \"title\": \"温暖相遇\", \"summary\": \"苏晴接纳林默，合租生活开始\"}, {\"chapter_number\": 3, \"title\": \"现实门槛\", \"summary\": \"面试受挫，第一次直面行业现实\"}, {\"chapter_number\": 4, \"title\": \"友情考验\", \"summary\": \"好友越过边界帮忙引发冲突\"}, {\"chapter_number\": 5, \"title\": \"破茧成蝶\", \"summary\": \"林默完成公开演出\"}], \"themes\": [\"梦想\", \"成长\", \"友情\"], \"conflicts\": [\"个人梦想与现实的冲突\", \"友情边界与互相理解\"]}', 'script:\n  schema_version: \"1.0\"\n  metadata:\n    title: \"星辰之下\"\n    original_novel: \"星辰之下\"\n    author: \"林默\"\n    language: \"zh-CN\"\n    target_format: \"screenplay\"\n    total_chapters: 5\n  characters:\n    - id: char_001\n      name: \"林默\"\n      role: \"主角\"\n      gender: \"男\"\n      age: 24\n      description: \"怀揣音乐梦想的年轻人\"\n    - id: char_002\n      name: \"苏晴\"\n      role: \"室友\"\n      gender: \"女\"\n      age: 25\n      description: \"行动力强的合租室友\"\n    - id: char_003\n      name: \"周亦辰\"\n      role: \"制作人\"\n      gender: \"男\"\n      age: 32\n      description: \"冷静的音乐制作人\"\n  locations:\n    - id: loc_001\n      name: \"地铁站\"\n      description: \"城市交通枢纽\"\n    - id: loc_002\n      name: \"合租出租屋\"\n      description: \"温馨的小房间\"\n    - id: loc_003\n      name: \"音乐公司面试间\"\n      description: \"冷白灯光\"\n  chapters:\n    - id: ch_001\n      title: \"初入城市\"\n      source_chapter_numbers: [1]\n      summary: \"林默初到城市\"\n      scenes:\n        - id: sc_001_001\n          title: \"地铁站相遇\"\n          location_id: loc_001\n          time: \"傍晚\"\n          characters: [char_001, char_002]\n          synopsis: \"林默初到城市感到迷茫\"\n          stage_directions:\n            - \"林默拖着行李箱走出地铁站，环顾四周。\"\n          dialogue:\n            - speaker_id: char_001\n              speaker_name: \"林默\"\n              line: \"这座城市，真的能实现我的梦想吗？\"\n              emotion: \"自言自语\"\n            - speaker_id: char_002\n              speaker_name: \"苏晴\"\n              line: \"需要帮忙吗？你看起来迷路了。\"\n              emotion: \"友好\"\n        - id: sc_001_002\n          title: \"出租屋夜谈\"\n          location_id: loc_002\n          time: \"夜晚\"\n          characters: [char_001, char_002]\n          synopsis: \"苏晴帮助林默安顿\"\n          stage_directions:\n            - \"窗外灯光落在旧吉他上。\"\n          dialogue:\n            - speaker_id: char_002\n              speaker_name: \"苏晴\"\n              line: \"先把今晚安顿好，梦想明天继续追。\"\n              emotion: \"温暖\"\n    - id: ch_002\n      title: \"温暖相遇\"\n      source_chapter_numbers: [2]\n      summary: \"合租生活开始\"\n      scenes:\n        - id: sc_002_001\n          title: \"清晨厨房\"\n          location_id: loc_002\n          time: \"早晨\"\n          characters: [char_001, char_002]\n          synopsis: \"两人聊起梦想\"\n          dialogue:\n            - speaker_id: char_002\n              speaker_name: \"苏晴\"\n              line: \"音乐这条路不好走，但你已经迈出第一步了。\"\n              emotion: \"鼓励\"\n    - id: ch_003\n      title: \"现实门槛\"\n      source_chapter_numbers: [3]\n      summary: \"面试受挫\"\n      scenes:\n        - id: sc_003_001\n          title: \"面试受挫\"\n          location_id: loc_003\n          time: \"下午\"\n          characters: [char_001, char_003]\n          synopsis: \"制作人打断演奏\"\n          stage_directions:\n            - \"冷白灯光很亮，林默攥紧背包带。\"\n          dialogue:\n            - speaker_id: char_003\n              speaker_name: \"周亦辰\"\n              line: \"技巧不错，但我听不到你自己的声音。\"\n              emotion: \"冷静\"\n            - speaker_id: char_001\n              speaker_name: \"林默\"\n              line: \"我可以再试一次，请给我一分钟。\"\n              emotion: \"紧张\"\n  adaptation_notes:\n    themes: [\"梦想\", \"成长\", \"友情\"]\n    conflicts: [\"个人梦想与现实的冲突\"]\n', '{\"templateId\": \"tv-drama\", \"scriptType\": \"影视剧\", \"adaptationStyle\": \"忠实改编\", \"contentOptions\": [\"保留对白\", \"强化冲突\"]}', NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `projects` VALUES (3, '山河令', '苏晴', 'analysis_completed', '{\"characters\": [{\"id\": \"char_001\", \"name\": \"顾晏\", \"role\": \"主角\", \"gender\": \"男\", \"age\": 28, \"description\": \"出身行伍的年轻将军\"}, {\"id\": \"char_002\", \"name\": \"江晚\", \"role\": \"主角\", \"gender\": \"女\", \"age\": 22, \"description\": \"女扮男装的天才谋士\"}], \"locations\": [{\"id\": \"loc_001\", \"name\": \"边塞军营\", \"description\": \"风沙漫天，营帐连营\"}, {\"id\": \"loc_002\", \"name\": \"京城府邸\", \"description\": \"雕梁画栋，暗藏杀机\"}], \"chapter_summaries\": [{\"chapter_number\": 1, \"title\": \"烽火狼烟\", \"summary\": \"边塞告急，顾晏奉命出征\"}, {\"chapter_number\": 2, \"title\": \"帐中谋\", \"summary\": \"江晚献计退敌获得赏识\"}, {\"chapter_number\": 3, \"title\": \"暗流涌动\", \"summary\": \"京城权力斗争波及前线\"}], \"themes\": [\"权谋\", \"战争\", \"家国\"], \"conflicts\": [\"战场生死\", \"朝堂暗斗\", \"身份之谜\"]}', NULL, '{\"templateId\": \"tv-drama\", \"scriptType\": \"影视剧\", \"adaptationStyle\": \"适度改编\", \"contentOptions\": [\"保留对白\", \"补充调度\"]}', NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `projects` VALUES (4, '深海秘密', '陈诚', 'created', NULL, NULL, '{\"templateId\": \"audio-drama\", \"scriptType\": \"广播剧\", \"adaptationStyle\": \"忠实改编\", \"contentOptions\": [\"保留对白\", \"补充环境音\"]}', NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `projects` VALUES (5, '废弃旧稿', '林默', 'created', NULL, NULL, NULL, '2025-06-04 08:00:00', '2026-06-07 14:38:35', '2026-06-07 14:38:35');
INSERT INTO `projects` VALUES (6, '霸总的意外新娘', '林默', 'script_completed', '{\"characters\": [{\"id\": \"char_001\", \"name\": \"陆辰\", \"role\": \"男主\", \"gender\": \"男\", \"age\": 28, \"description\": \"商界大佬，外冷内热\"}, {\"id\": \"char_002\", \"name\": \"夏浅浅\", \"role\": \"女主\", \"gender\": \"女\", \"age\": 23, \"description\": \"普通上班族，乐观开朗\"}], \"locations\": [{\"id\": \"loc_001\", \"name\": \"陆氏集团\", \"description\": \"摩天大楼顶层办公室\"}, {\"id\": \"loc_002\", \"name\": \"民政局门口\", \"description\": \"阳光明媚的早晨\"}], \"chapter_summaries\": [{\"chapter_number\": 1, \"title\": \"阴差阳错\", \"summary\": \"一场误会，两人被迫临时领证\"}, {\"chapter_number\": 2, \"title\": \"隐藏身份\", \"summary\": \"陆辰的真实身份开始浮出水面\"}, {\"chapter_number\": 3, \"title\": \"终极考验\", \"summary\": \"商业陷阱让两人面临抉择\"}], \"themes\": [\"爱情\", \"轻喜剧\", \"反转\"], \"conflicts\": [\"身份悬殊\", \"第三方阴谋\"]}', 'script:\n  schema_version: \"1.0\"\n  metadata:\n    title: \"霸总的意外新娘\"\n    target_format: \"short_drama\"\n    template_id: \"short-drama\"\n    total_chapters: 3\n  characters:\n    - id: char_001\n      name: \"陆辰\"\n      role: \"男主\"\n    - id: char_002\n      name: \"夏浅浅\"\n      role: \"女主\"\n  locations:\n    - id: loc_001\n      name: \"陆氏集团\"\n    - id: loc_002\n      name: \"民政局门口\"\n  chapters:\n    - id: ep_001\n      title: \"合约领证\"\n      source_chapter_numbers: [1]\n      summary: \"误会领证\"\n      scenes:\n        - id: sc_001_001\n          title: \"民政局前的意外\"\n          location_id: loc_002\n          time: \"早晨\"\n          characters: [char_001, char_002]\n          synopsis: \"乌龙相遇\"\n          dialogue:\n            - speaker_id: char_001\n              speaker_name: \"陆辰\"\n              line: \"既然命运安排我们相遇，那就先把证领了。\"\n              emotion: \"冷漠\"\n            - speaker_id: char_002\n              speaker_name: \"夏浅浅\"\n              line: \"你疯了吗？我们才认识五分钟！\"\n              emotion: \"震惊\"\n        - id: sc_001_002\n          title: \"霸王条款\"\n          location_id: loc_001\n          time: \"上午\"\n          characters: [char_001, char_002]\n          synopsis: \"陆辰拿出合同\"\n          stage_directions:\n            - \"陆辰推开合同文件，起身走向窗边。\"\n          dialogue:\n            - speaker_id: char_002\n              speaker_name: \"夏浅浅\"\n              line: \"领证还要签合同？\"\n              emotion: \"疑惑\"\n            - speaker_id: char_001\n              speaker_name: \"陆辰\"\n              line: \"做我的挂名太太，六个月后各不相欠。\"\n              emotion: \"掌控\"\n  adaptation_notes:\n    themes: [\"爱情\", \"轻喜剧\"]\n', '{\"templateId\": \"short-drama\", \"scriptType\": \"短剧\", \"adaptationStyle\": \"适度改编\", \"contentOptions\": [\"强化开场冲突\", \"突出反转节点\"]}', NULL, '2026-06-07 14:38:35', '2026-06-07 14:38:35');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_users_email`(`email` ASC) USING BTREE,
  INDEX `ix_users_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'mysql-test', 'mysql@test.com', '$2b$12$7Fx9KFM9uLSIwdXuJ2sUdO4ouk2UCiABs/jHLUkrDGK4RLsK4yM4S', '2026-06-07 13:36:45');

SET FOREIGN_KEY_CHECKS = 1;
