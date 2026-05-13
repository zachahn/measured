module TestTasks
  extend Rake::DSL

  task :test do
    failures = []

    check_name = ->(path, expected_name) do
      content = File.read(path)
      unless content.start_with?("---\n")
        failures << "#{path}: missing YAML frontmatter"
        return
      end

      _, frontmatter, _ = content.split(/^---\s*$/, 3)
      match = frontmatter.match(/^name:\s*(\S+)\s*$/)
      actual_name = match && match[1]

      if actual_name.nil?
        failures << "#{path}: missing `name` in frontmatter"
      elsif actual_name != expected_name
        failures << "#{path}: name `#{actual_name}` does not match expected `#{expected_name}`"
      end
    end

    Dir.glob("source/skills/**/SKILL.md").each do |path|
      check_name.call(path, File.basename(File.dirname(path)))
    end

    Dir.glob("source/agents/*.md").each do |path|
      check_name.call(path, File.basename(path, ".md"))
    end

    if failures.empty?
      puts "All skill and agent names match."
    else
      failures.each { |f| puts "FAIL: #{f}" }
      abort "#{failures.size} file(s) failed validation"
    end
  end
end

module BuildTasks
  extend Rake::DSL

  task :build do
    require "erb"
    require "fileutils"

    Dir.glob("source/**/*").each do |source|
      dest = source.sub(%r{\Asource/}, "")
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
