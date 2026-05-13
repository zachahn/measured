module TestTasks
  extend Rake::DSL

  task :test do
    require "yaml"

    failures = []

    Dir.glob("source/**/SKILL.md").each do |path|
      expected_name = File.basename(File.dirname(path))

      content = File.read(path)
      unless content.start_with?("---\n")
        failures << "#{path}: missing YAML frontmatter"
        next
      end

      _, frontmatter, _ = content.split(/^---\s*$/, 3)
      data = YAML.safe_load(frontmatter)
      actual_name = data && data["name"]

      if actual_name.nil?
        failures << "#{path}: missing `name` in frontmatter"
      elsif actual_name != expected_name
        failures << "#{path}: name `#{actual_name}` does not match directory `#{expected_name}`"
      end
    end

    if failures.empty?
      puts "All skill names match their directories."
    else
      failures.each { |f| puts "FAIL: #{f}" }
      abort "#{failures.size} skill(s) failed validation"
    end
  end
end

module BuildTasks
  extend Rake::DSL

  task :build do
    require "erb"
    require "fileutils"

    Dir.glob("source/**/*").each do |source|
      dest = source.sub(%r{\Asource/}, "skills/")
      destdir = File.dirname(dest)
      next if dest == source
      next if File.directory?(source)

      puts "== #{source}"

      original = File.read(source)
      erb = ERB.new(original)
      built = erb.result(binding)

      FileUtils.mkdir_p(destdir)
      File.write(dest, built)
    rescue => e
      puts "ERROR: #{source}"
      puts e
      next
    end
  end
end
